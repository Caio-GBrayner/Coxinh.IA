import asyncio

from fastmcp import FastMCP
import pytest

from mcp_server.errors import tool_error
from src import mcp_client
from src.mcp_client import McpToolClient, McpToolError


def create_probe_server() -> FastMCP:
    mcp = FastMCP("probe", mask_error_details=True)

    @mcp.tool
    def echo(value: int) -> dict:
        return {"value": value}

    @mcp.tool
    def contract_error() -> dict:
        raise tool_error("invalid_input", "bad input", field="value")

    @mcp.tool
    def unexpected_error() -> dict:
        raise RuntimeError("segredo-interno")

    return mcp


def test_call_returns_the_structured_result():
    client = McpToolClient(create_probe_server())

    assert client.call("echo", {"value": 3}) == {"value": 3}


def test_contract_errors_keep_code_message_and_details():
    client = McpToolClient(create_probe_server())

    with pytest.raises(McpToolError) as error:
        client.call("contract_error", {})

    assert error.value.code == "invalid_input"
    assert error.value.message == "bad input"
    assert error.value.details == {"field": "value"}


def test_schema_validation_errors_become_invalid_input():
    client = McpToolClient(create_probe_server())

    with pytest.raises(McpToolError) as error:
        client.call("echo", {"value": "not-a-number"})

    assert error.value.code == "invalid_input"


def test_unexpected_errors_become_masked_tool_errors():
    client = McpToolClient(create_probe_server())

    with pytest.raises(McpToolError) as error:
        client.call("unexpected_error", {})

    assert error.value.code == "tool_error"
    assert "segredo-interno" not in str(error.value)


def test_call_works_when_an_event_loop_is_already_running():
    client = McpToolClient(create_probe_server())

    async def inside_a_loop():
        return client.call("echo", {"value": 7})

    assert asyncio.run(inside_a_loop()) == {"value": 7}


def test_default_client_uses_the_configured_url(monkeypatch):
    monkeypatch.setattr(mcp_client, "load_dotenv", lambda: None)
    monkeypatch.setenv("MCP_SERVER_URL", "http://mcp:8000/mcp")

    client = mcp_client.get_tool_client()

    assert client._target == "http://mcp:8000/mcp"


def test_default_client_runs_in_process_without_a_url(monkeypatch):
    monkeypatch.setattr(mcp_client, "load_dotenv", lambda: None)
    monkeypatch.delenv("MCP_SERVER_URL", raising=False)

    client = mcp_client.get_tool_client()

    assert isinstance(client._target, FastMCP)


def test_default_client_is_cached_until_reset(monkeypatch):
    monkeypatch.setattr(mcp_client, "load_dotenv", lambda: None)
    monkeypatch.delenv("MCP_SERVER_URL", raising=False)

    first = mcp_client.get_tool_client()
    assert mcp_client.get_tool_client() is first

    mcp_client.reset_default_client()
    assert mcp_client.get_tool_client() is not first
