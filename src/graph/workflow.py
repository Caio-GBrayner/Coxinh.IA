from copy import deepcopy
from threading import Lock
from typing import Any, TypeAlias

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from src.graph.graph import build_graph
from src.graph.impasse import ImpasseDecision, StateVersionConflict
from src.state import RecipeState


WorkflowResult: TypeAlias = dict[str, Any]


class InMemoryWorkflow:
    def __init__(
        self,
        *,
        checkpointer: BaseCheckpointSaver | None = None,
    ) -> None:
        self._checkpointer = (
            MemorySaver() if checkpointer is None else checkpointer
        )
        self._graph = build_graph(checkpointer=self._checkpointer)
        self._thread_locks: dict[str, Lock] = {}
        self._thread_locks_guard = Lock()
        self._processed_decisions: dict[
            tuple[str, str], tuple[str, WorkflowResult]
        ] = {}

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

    def submit_impasse_decision(
        self,
        thread_id: str,
        decision: ImpasseDecision,
    ) -> WorkflowResult:
        run_config = self._run_config(thread_id)
        fingerprint = decision.model_dump_json(exclude={"idempotency_key"})
        idempotency_key = (thread_id, decision.idempotency_key)

        with self._thread_lock(thread_id):
            processed = self._processed_decisions.get(idempotency_key)
            if processed is not None:
                previous_fingerprint, previous_result = processed
                if previous_fingerprint != fingerprint:
                    raise ValueError(
                        "An idempotency key cannot be reused for a different decision."
                    )
                return deepcopy(previous_result)

            snapshot = self._graph.get_state(run_config)
            if not snapshot.values:
                raise KeyError(f"No workflow exists for thread_id '{thread_id}'.")

            current_state = snapshot.values
            if current_state.get("status") != "awaiting_user":
                raise ValueError("The workflow is not waiting for an Impasse decision.")

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

            result = self._graph.invoke(
                Command(resume=decision.model_dump()),
                config=run_config,
            )
            result_copy = deepcopy(result)
            self._processed_decisions[idempotency_key] = (
                fingerprint,
                result_copy,
            )
            return result_copy

    def _thread_lock(self, thread_id: str) -> Lock:
        with self._thread_locks_guard:
            if thread_id not in self._thread_locks:
                self._thread_locks[thread_id] = Lock()
            return self._thread_locks[thread_id]

    @staticmethod
    def _run_config(thread_id: str) -> RunnableConfig:
        if not isinstance(thread_id, str) or not thread_id.strip():
            raise ValueError("thread_id must not be empty.")
        return {"configurable": {"thread_id": thread_id}}
