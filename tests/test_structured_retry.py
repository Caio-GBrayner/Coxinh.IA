import httpx
import pytest
from groq import BadRequestError

from src.utils import llm_adapter
from src.utils.llm_adapter import invoke_structured


def bad_request(message: str) -> BadRequestError:
    response = httpx.Response(400, request=httpx.Request("POST", "https://api.test"))
    return BadRequestError(message, response=response, body=None)


class FlakyChain:
    """Falha com os erros programados e depois devolve o resultado."""

    def __init__(self, errors, result="ok"):
        self.errors = list(errors)
        self.result = result
        self.calls = 0

    def invoke(self, payload):
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return self.result


def test_retries_when_the_model_does_not_call_the_tool():
    chain = FlakyChain([bad_request("tool_use_failed: no tool"), bad_request("tool_use_failed")])

    assert invoke_structured(chain, {}) == "ok"
    assert chain.calls == 3


def test_raises_after_all_attempts_fail():
    chain = FlakyChain([bad_request("tool_use_failed")] * 5)

    with pytest.raises(BadRequestError):
        invoke_structured(chain, {})
    assert chain.calls == llm_adapter.STRUCTURED_MAX_ATTEMPTS


def test_other_bad_requests_are_not_retried():
    chain = FlakyChain([bad_request("invalid api key")])

    with pytest.raises(BadRequestError):
        invoke_structured(chain, {})
    assert chain.calls == 1
