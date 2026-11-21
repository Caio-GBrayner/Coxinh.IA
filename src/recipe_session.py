from src.graph.impasse import ImpasseDecision
from src.graph.workflow import InMemoryWorkflow, WorkflowResult
from src.recipe_history import SessionRecipeHistory
from src.state import RecipeState


class RecipeSession:
    """Coordena as execuções e o histórico de uma sessão."""

    def __init__(self) -> None:
        """Cria o workflow e o histórico que a sessão vai reutilizar."""
        self._workflow = InMemoryWorkflow()
        self.history = SessionRecipeHistory()

    def start(self, initial_state: RecipeState) -> WorkflowResult:
        """Inicia um pedido e salva a receita se ele for concluído."""
        result = self._workflow.start(initial_state)
        return self._save_if_completed(result)

    def get_state(self, thread_id: str) -> WorkflowResult:
        """Consulta o estado de um pedido da sessão."""
        return self._workflow.get_state(thread_id)

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