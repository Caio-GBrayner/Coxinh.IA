from copy import deepcopy
from threading import Lock
from typing import Any, Literal, TypeAlias

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.types import Command

from src.graph.builder import build_graph
from src.graph.guardrail import InputBlocked, check_text
from src.graph.impasse import (
    IdempotencyKeyReuse,
    ImpasseDecision,
    ResumeLimitReached,
    StateVersionConflict,
    WorkflowNotPaused,
)
from src.observability import langfuse_callbacks
from src.persistence.decision_store import (
    DecisionStore,
    InMemoryDecisionStore,
    VersionAlreadyClaimed,
)
from src.state import RecipeState


WorkflowResult: TypeAlias = dict[str, Any]
DecisionStatus: TypeAlias = Literal["new", "pending", "done"]

# Ciclos de revisão por conversa (o primeiro mais as retomadas). Depois disso,
# "resume" é recusado e restam aceitar, salvar ou encerrar: nunca há laço infinito.
MAX_REVIEW_CYCLES = 4
RECOVERY_MESSAGE = (
    "A última tentativa não terminou por um erro técnico. "
    "Você pode tentar de novo, aceitar a proposta atual ou encerrar."
)
FINISHED_STATUSES = ("completed", "cancelled", "blocked")


def resume_allowed(state: dict[str, Any]) -> bool:
    """Diz se ainda cabe uma retomada nesta conversa."""
    max_revisions = state.get("max_revisions") or 1
    return (state.get("total_attempts") or 0) < max_revisions * MAX_REVIEW_CYCLES


def project_serializer() -> JsonPlusSerializer:
    """Autoriza no checkpoint os modelos do projeto, evitando o aviso do LangGraph."""
    return JsonPlusSerializer(
        allowed_msgpack_modules=[
            ("src.schemas", "Recipe"),
            ("src.schemas", "SubChefEvaluation"),
        ]
    )



class RecipeWorkflow:
    """Executa o grafo com checkpointer e registro de decisões injetáveis.

    Sem argumentos, tudo fica em memória (testes e modo sem persistência). Com
    um checkpointer SQLite e um `SqliteDecisionStore`, a execução sobrevive a
    reinícios: um impasse continua pausado e pode ser decidido depois.
    As travas por `thread_id` são locais ao processo; a aplicação roda em um
    único processo (decisão D4) e a unicidade de versão no banco é a garantia
    final contra duas decisões para a mesma versão.
    """

    def __init__(
        self,
        *,
        checkpointer: BaseCheckpointSaver | None = None,
        decision_store: DecisionStore | None = None,
    ) -> None:
        self._checkpointer = (
            MemorySaver(serde=project_serializer())
            if checkpointer is None
            else checkpointer
        )
        self._decisions = (
            InMemoryDecisionStore() if decision_store is None else decision_store
        )
        self._graph = build_graph(checkpointer=self._checkpointer)
        self._callbacks = langfuse_callbacks()
        self._thread_locks: dict[str, Lock] = {}
        self._thread_locks_guard = Lock()

    def start(self, initial_state: RecipeState) -> WorkflowResult:
        thread_id = initial_state["thread_id"]
        run_config = self._run_config(thread_id)
        with self._thread_lock(thread_id):
            existing_state = self._graph.get_state(run_config)
            if existing_state.values:
                raise ValueError("A workflow already exists for this thread_id.")
            return self._graph.invoke(initial_state, config=run_config)

    def get_state(self, thread_id: str) -> WorkflowResult:
        run_config = self._run_config(thread_id)
        with self._thread_lock(thread_id):
            snapshot = self._graph.get_state(run_config)
            if not snapshot.values:
                raise KeyError(f"No workflow exists for thread_id '{thread_id}'.")
            return deepcopy(snapshot.values)

    def decision_status(
        self,
        thread_id: str,
        decision: ImpasseDecision,
    ) -> DecisionStatus:
        """Diz se a decisão é nova, está em andamento ou já foi aplicada."""
        stored = self._decisions.get(thread_id, decision.idempotency_key)
        if stored is None:
            return "new"
        if stored.fingerprint != _fingerprint(decision):
            raise IdempotencyKeyReuse(
                "An idempotency key cannot be reused for a different decision."
            )
        return "done" if stored.completed else "pending"

    def submit_impasse_decision(
        self,
        thread_id: str,
        decision: ImpasseDecision,
    ) -> WorkflowResult:
        """Aplica a decisão ou continua uma retomada já registrada no checkpoint."""
        run_config = self._run_config(thread_id)
        fingerprint = _fingerprint(decision)
        key = decision.idempotency_key

        with self._thread_lock(thread_id):
            stored = self._decisions.get(thread_id, key)
            if stored is not None:
                if stored.fingerprint != fingerprint:
                    raise IdempotencyKeyReuse(
                        "An idempotency key cannot be reused for a different decision."
                    )
                if stored.completed and stored.result is not None:
                    return deepcopy(stored.result)

            snapshot = self._graph.get_state(run_config)
            if not snapshot.values:
                raise KeyError(f"No workflow exists for thread_id '{thread_id}'.")

            current_state = snapshot.values
            continuing = (
                current_state.get("status") == "in_revision"
                and snapshot.next
                and current_state.get("last_impasse_decision_key") == key
            )
            if not continuing and self._stopped_after_decision(snapshot):
                # Uma decisão anterior começou a rodar e falhou no meio. Em vez de
                # recusar tudo, devolve a conversa ao Impasse e aplica esta decisão.
                self._restore_pause(run_config)
                snapshot = self._graph.get_state(run_config)
                current_state = snapshot.values

            if continuing:
                # A decisão já entrou no checkpoint, mas a execução parou depois.
                if current_state.get("last_impasse_decision_fingerprint") != fingerprint:
                    raise IdempotencyKeyReuse(
                        "An idempotency key cannot be reused for a different decision."
                    )
                graph_input = None
            else:
                if current_state.get("status") != "awaiting_user":
                    raise WorkflowNotPaused(
                        "The workflow is not waiting for an Impasse decision."
                    )

                current_version = current_state.get("state_version")
                if (
                    not isinstance(current_version, int)
                    or isinstance(current_version, bool)
                    or current_version < 0
                ):
                    raise ValueError("state_version must be a non-negative integer.")
                if decision.expected_state_version != current_version:
                    raise StateVersionConflict(
                        decision.expected_state_version,
                        current_version,
                    )
                if decision.action == "resume" and not resume_allowed(current_state):
                    raise ResumeLimitReached(
                        "Limite de novas tentativas atingido. "
                        "Aceite a proposta atual ou encerre a criação."
                    )
                # Antes da reserva e do grafo: um texto recusado não gasta a versão
                # nem a chave, e não fica guardado como resposta do Impasse.
                _check_decision_text(decision)
                self._claim(thread_id, decision, fingerprint, current_version)
                graph_input = Command(resume=decision.model_dump())

            try:
                result = self._graph.invoke(graph_input, config=run_config)
            except BaseException:
                # Sem reserva pendente, a mesma chave pode tentar de novo; se a
                # decisão já entrou no checkpoint, a retentativa segue o caminho
                # de continuação acima.
                self._decisions.release(thread_id, key)
                raise

            result_copy = deepcopy(result)
            self._decisions.complete(
                thread_id,
                key,
                decision.expected_state_version,
                fingerprint,
                result_copy,
            )
            return deepcopy(result_copy)

    def is_recoverable(self, thread_id: str) -> bool:
        """Diz se a conversa parou no meio depois de uma decisão e pode voltar ao Impasse."""
        run_config = self._run_config(thread_id)
        with self._thread_lock(thread_id):
            snapshot = self._graph.get_state(run_config)
            return bool(snapshot.values) and self._stopped_after_decision(snapshot)

    def recover(self, thread_id: str) -> WorkflowResult:
        """Devolve ao Impasse uma conversa que parou no meio; senão, só lê o estado."""
        run_config = self._run_config(thread_id)
        with self._thread_lock(thread_id):
            snapshot = self._graph.get_state(run_config)
            if not snapshot.values:
                raise KeyError(f"No workflow exists for thread_id '{thread_id}'.")
            if self._stopped_after_decision(snapshot):
                self._restore_pause(run_config)
                snapshot = self._graph.get_state(run_config)
            return deepcopy(snapshot.values)

    @staticmethod
    def _stopped_after_decision(snapshot: Any) -> bool:
        """Execução parada no meio (há próximo nó) depois de uma decisão do Impasse.

        Quem chama segura a trava da thread, então nada está rodando agora: se há
        um próximo nó pendente, a execução anterior foi interrompida por uma falha.
        """
        state = snapshot.values
        return (
            bool(snapshot.next)
            and state.get("status") not in ("awaiting_user", *FINISHED_STATUSES)
            and bool(state.get("last_impasse_decision_key"))
        )

    def _restore_pause(self, run_config: RunnableConfig) -> None:
        """Volta ao nó do Impasse e roda até a pausa, preservando a versão do estado."""
        self._graph.update_state(
            run_config,
            {
                "status": "awaiting_user",
                "user_action": "save",
                "last_error": RECOVERY_MESSAGE,
            },
            as_node="impasse",
        )
        self._graph.invoke(None, config=run_config)

    def _claim(
        self,
        thread_id: str,
        decision: ImpasseDecision,
        fingerprint: str,
        current_version: int,
    ) -> None:
        """Reserva a versão no registro; substitui uma reserva órfã de uma queda."""
        try:
            self._decisions.claim(
                thread_id, decision.idempotency_key, current_version, fingerprint
            )
        except VersionAlreadyClaimed as exc:
            if exc.existing.completed:
                raise StateVersionConflict(
                    decision.expected_state_version, current_version + 1
                ) from exc
            # Reserva pendente com o estado ainda nesta versão: sobrou de uma
            # execução interrompida, pois este processo detém a trava da thread.
            self._decisions.release(thread_id, exc.existing.idempotency_key)
            self._decisions.claim(
                thread_id, decision.idempotency_key, current_version, fingerprint
            )

    def _thread_lock(self, thread_id: str) -> Lock:
        with self._thread_locks_guard:
            if thread_id not in self._thread_locks:
                self._thread_locks[thread_id] = Lock()
            return self._thread_locks[thread_id]

    def _run_config(self, thread_id: str) -> RunnableConfig:
        if not isinstance(thread_id, str) or not thread_id.strip():
            raise ValueError("thread_id must not be empty.")
        return {
            "configurable": {"thread_id": thread_id},
            "callbacks": self._callbacks,
        }


# Nome antigo, mantido porque testes e módulos ainda o importam.
InMemoryWorkflow = RecipeWorkflow


def _check_decision_text(decision: ImpasseDecision) -> None:
    parts = [*decision.ingredient_additions, decision.user_guidance or ""]
    text = "\n".join(part for part in parts if part)
    if not text:
        return
    result = check_text(text, "impasse")
    if not result.allowed:
        raise InputBlocked(result)


def _fingerprint(decision: ImpasseDecision) -> str:
    return decision.model_dump_json(exclude={"idempotency_key"})
