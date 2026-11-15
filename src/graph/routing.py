from typing import Literal

from src.schemas import AvaliacaoSubchef
from src.state import ReceitaState


DestinoSubchef = Literal["chef", "cook", "impasse"]


def registrar_avaliacao_subchef(estado: ReceitaState) -> ReceitaState:
    """Record a valid review and update cycle and conversation counters."""
    if estado.get("status") != "in_revision":
        raise ValueError(
            "A SubChef evaluation can only be recorded while the workflow is in review."
        )

    avaliacao = estado.get("avaliacao")
    if not isinstance(avaliacao, AvaliacaoSubchef):
        raise TypeError("State must contain a valid SubChef evaluation.")

    revision_count = estado.get("revision_count")
    total_attempts = estado.get("total_attempts")
    max_revisions = estado.get("max_revisions")

    if not isinstance(revision_count, int) or isinstance(revision_count, bool):
        raise ValueError("revision_count must be a non-negative integer.")
    if revision_count < 0:
        raise ValueError("revision_count must be a non-negative integer.")
    if not isinstance(total_attempts, int) or isinstance(total_attempts, bool):
        raise ValueError("total_attempts must be a non-negative integer.")
    if total_attempts < 0:
        raise ValueError("total_attempts must be a non-negative integer.")
    if not isinstance(max_revisions, int) or isinstance(max_revisions, bool):
        raise ValueError("max_revisions must be a positive integer.")
    if max_revisions < 1:
        raise ValueError("max_revisions must be a positive integer.")
    if revision_count > max_revisions:
        raise ValueError("revision_count cannot exceed max_revisions.")

    estado_atualizado: ReceitaState = {
        **estado,
        "total_attempts": total_attempts + 1,
    }

    if avaliacao.decision == "approved":
        estado_atualizado["status"] = "approved"
    elif revision_count < max_revisions:
        estado_atualizado["revision_count"] = revision_count + 1
        estado_atualizado["status"] = "in_revision"
    else:
        estado_atualizado["status"] = "awaiting_user"

    return estado_atualizado


def route_after_subchef(estado: ReceitaState) -> DestinoSubchef:
    """Select the next node from the recorded SubChef evaluation and status."""
    avaliacao = estado.get("avaliacao")
    if not isinstance(avaliacao, AvaliacaoSubchef):
        raise TypeError("State must contain a valid SubChef evaluation.")

    status = estado.get("status")
    if avaliacao.decision == "approved" and status == "approved":
        return "cook"
    if avaliacao.decision == "rejected" and status == "in_revision":
        return "chef"
    if avaliacao.decision == "rejected" and status == "awaiting_user":
        return "impasse"

    raise ValueError("The SubChef decision does not match the workflow status.")
