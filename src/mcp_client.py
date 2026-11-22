import asyncio
from collections.abc import Coroutine
from concurrent.futures import ThreadPoolExecutor
import json
import os
from threading import Lock
from typing import Any, TypeVar

from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.exceptions import ToolError


DEFAULT_TIMEOUT_SECONDS = 60.0

T = TypeVar("T")


class McpToolError(RuntimeError):
    """Erro devolvido por uma ferramenta MCP, com o código do contrato."""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.details = details or {}


def _parse_tool_error(exc: ToolError) -> McpToolError:
    text = str(exc)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = None

    if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
        error = payload["error"]
        return McpToolError(
            str(error.get("code", "tool_error")),
            str(error.get("message", "")),
            error.get("details"),
        )
    # Erros de validação do esquema são gerados pelo FastMCP, fora do contrato.
    if "validation error" in text:
        return McpToolError("invalid_input", text)
    return McpToolError("tool_error", text)


def _run_sync(coroutine: Coroutine[Any, Any, T]) -> T:
    """Executa a corrotina também quando já existe um loop em andamento."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coroutine).result()


class McpToolClient:
    """Cliente síncrono para chamar ferramentas do servidor MCP.

    `target` é um servidor FastMCP (execução em processo) ou a URL do servidor
    HTTP, por exemplo `http://mcp:8000/mcp`.
    """

    def __init__(
        self,
        target: Any,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._target = target
        self._timeout = timeout

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return _run_sync(self._call(name, arguments))

    async def _call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        async with Client(self._target, timeout=self._timeout) as client:
            try:
                result = await client.call_tool(name, arguments)
            except ToolError as exc:
                raise _parse_tool_error(exc) from exc

        structured = result.structured_content
        if not isinstance(structured, dict):
            raise McpToolError("tool_error", "The tool returned no structured content.")
        return structured


_default_client: McpToolClient | None = None
_default_lock = Lock()


def _build_default_client() -> McpToolClient:
    load_dotenv()
    url = os.getenv("MCP_SERVER_URL", "").strip()
    if url:
        return McpToolClient(url)

    # Sem URL, o servidor roda no próprio processo (desenvolvimento e testes).
    from mcp_server.server import build_default_server

    return McpToolClient(build_default_server())


def get_tool_client() -> McpToolClient:
    global _default_client
    with _default_lock:
        if _default_client is None:
            _default_client = _build_default_client()
        return _default_client


def reset_default_client() -> None:
    """Descarta o cliente padrão. Usado pelos testes para isolar o índice de imagens."""
    global _default_client
    with _default_lock:
        _default_client = None
