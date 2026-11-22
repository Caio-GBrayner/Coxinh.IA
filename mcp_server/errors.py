import json
from typing import Any, Literal

from fastmcp.exceptions import ToolError


ErrorCode = Literal[
    "invalid_input",
    "workflow_not_found",
    "workflow_not_paused",
    "state_version_conflict",
    "idempotency_key_reuse",
    "provider_unavailable",
]


def tool_error(code: ErrorCode, message: str, **details: Any) -> ToolError:
    """Cria o erro de ferramenta no formato do contrato.

    O corpo é um JSON `{"error": {"code", "message", "details"?}}`. Só este
    formato chega ao cliente sem mascaramento.
    """
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return ToolError(json.dumps({"error": error}, ensure_ascii=False))
