import base64
import json

import httpx
import pytest
from pydantic import SecretStr

from mcp_server.images import ImageProviderError, SimulatedImageProvider
from mcp_server.openrouter import (
    OPENROUTER_IMAGES_URL,
    OpenRouterImageProvider,
    build_image_provider_from_env,
)


PNG_BYTES = b"\x89PNG\r\n\x1a\nfake"


def ok_transport(calls):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "id": "gen-1",
                "data": [
                    {
                        "b64_json": base64.b64encode(PNG_BYTES).decode(),
                        "media_type": "image/png",
                    }
                ],
            },
        )

    return httpx.MockTransport(handler)


def make_provider(tmp_path, transport, **kwargs):
    return OpenRouterImageProvider(
        SecretStr("sk-test"), storage_dir=tmp_path, transport=transport, **kwargs
    )


def test_generates_saves_file_and_returns_reference(tmp_path):
    calls = []
    provider = make_provider(tmp_path, ok_transport(calls))

    image = provider.generate("uma coxinha", idempotency_key="abc123")

    assert image.reference == "images/abc123.png"
    assert image.request_id == "gen-1"
    assert (tmp_path / "abc123.png").read_bytes() == PNG_BYTES
    request = calls[0]
    assert str(request.url) == OPENROUTER_IMAGES_URL
    assert request.headers["Authorization"] == "Bearer sk-test"
    body = json.loads(request.content)
    assert body["model"] == "recraft/recraft-v4.1-flash-v2:free"
    assert body["prompt"] == "uma coxinha"


def test_existing_file_is_reused_without_calling_the_api(tmp_path):
    (tmp_path / "abc123.png").write_bytes(PNG_BYTES)
    calls = []
    provider = make_provider(tmp_path, ok_transport(calls))

    image = provider.generate("uma coxinha", idempotency_key="abc123")

    assert image.reference == "images/abc123.png"
    assert calls == []


def test_http_error_raises_provider_error(tmp_path):
    transport = httpx.MockTransport(lambda r: httpx.Response(429, text="rate limited"))
    provider = make_provider(tmp_path, transport)

    with pytest.raises(ImageProviderError, match="429"):
        provider.generate("uma coxinha", idempotency_key="abc123")
    assert list(tmp_path.iterdir()) == []


def test_response_without_image_raises_provider_error(tmp_path):
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json={"data": []}))
    provider = make_provider(tmp_path, transport)

    with pytest.raises(ImageProviderError, match="sem imagem"):
        provider.generate("uma coxinha", idempotency_key="abc123")


def test_network_failure_raises_provider_error(tmp_path):
    def boom(request):
        raise httpx.ConnectTimeout("timeout")

    provider = make_provider(tmp_path, httpx.MockTransport(boom))

    with pytest.raises(ImageProviderError, match="rede"):
        provider.generate("uma coxinha", idempotency_key="abc123")


def test_paid_model_is_refused_unless_allowed(tmp_path):
    with pytest.raises(ValueError, match="pago"):
        make_provider(tmp_path, ok_transport([]), model="recraft/recraft-v4.1-flash-v2")

    provider = make_provider(
        tmp_path, ok_transport([]), model="recraft/recraft-v4.1-flash-v2", allow_paid=True
    )
    assert provider.name == "openrouter:recraft/recraft-v4.1-flash-v2"


def test_env_without_key_uses_simulated_provider(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    assert isinstance(build_image_provider_from_env(), SimulatedImageProvider)


def test_env_with_key_uses_openrouter(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    monkeypatch.setenv("OPENROUTER_IMAGE_MODEL", "recraft/recraft-v4.1-flash-v2:free")
    monkeypatch.setenv("IMAGE_STORAGE_DIR", str(tmp_path))
    provider = build_image_provider_from_env()
    assert isinstance(provider, OpenRouterImageProvider)
