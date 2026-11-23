from src.graph.impasse import ImpasseDecision
from src.graph.workflow import DecisionStatus, RecipeWorkflow, WorkflowResult
from src.recipe_history import SessionRecipeHistory
from src.state import RecipeState


class RecipeSession:
    """Coordena as execuções e o histórico de uma sessão."""

    def __init__(
        self,
        *,
        workflow: RecipeWorkflow | None = None,
        history: SessionRecipeHistory | None = None,
    ) -> None:
        """Usa o workflow e o histórico dados, ou cria versões em memória."""
        self._workflow = RecipeWorkflow() if workflow is None else workflow
        self.history = SessionRecipeHistory() if history is None else history

    def start(self, initial_state: RecipeState) -> WorkflowResult:
        """Inicia um pedido e salva a receita se ele for concluído."""
        result = self._workflow.start(initial_state)
        return self._save_if_completed(result)

    def get_state(self, thread_id: str) -> WorkflowResult:
        """Consulta o estado de um pedido da sessão."""
        return self._workflow.get_state(thread_id)

    def decision_status(
        self,
        thread_id: str,
        decision: ImpasseDecision,
    ) -> DecisionStatus:
        """Diz se a decisão é nova, está em andamento ou já foi aplicada."""
        return self._workflow.decision_status(thread_id, decision)

    def submit_impasse_decision(
        self,
        thread_id: str,
        decision: ImpasseDecision,
    ) -> WorkflowResult:
        """Aplica a decisão do usuário e salva a receita se ela for concluída."""
        result = self._workflow.submit_impasse_decision(thread_id, decision)
        return self._save_if_completed(result)

    def _save_if_completed(self, result: WorkflowResult) -> WorkflowResult:
        """Registra somente resultados concluídos e devolve o estado à aplicação."""
        if result["status"] == "completed":
            self.history.save_completed(result)

        return result
