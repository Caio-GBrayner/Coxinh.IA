"""Provedor real de imagem via OpenRouter (Image API).

Endpoint: POST https://openrouter.ai/api/v1/images com `model` e `prompt`.
A resposta traz a imagem em base64 em `data[0].b64_json`; ela é gravada em
disco e o provedor devolve só a referência, nunca os bytes (contrato MCP).

Garantias:
- o arquivo é nomeado pela chave de idempotência; se já existir, nenhuma chamada
  é feita, inclusive depois de reiniciar o servidor;
- a gravação é atômica (arquivo temporário e rename);
- modelos pagos são recusados, a menos que OPENROUTER_ALLOW_PAID=true. Não há
  troca automática para variante paga.
"""

import base64
import binascii
import os
from pathlib import Path
import tempfile

import httpx
from pydantic import SecretStr

from mcp_server.images import ImageProviderError, ProviderImage


OPENROUTER_IMAGES_URL = "https://openrouter.ai/api/v1/images"
DEFAULT_IMAGE_MODEL = "recraft/recraft-v4.1-flash-v2:free"
DEFAULT_STORAGE_DIR = "data/images"
DEFAULT_TIMEOUT_SECONDS = 120.0

EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}


class OpenRouterImageProvider:
    """Gera a imagem no OpenRouter e grava o arquivo em `storage_dir`."""

    def __init__(
        self,
        api_key: SecretStr,
        *,
        model: str = DEFAULT_IMAGE_MODEL,
        storage_dir: str | Path = DEFAULT_STORAGE_DIR,
        allow_paid: bool = False,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not model.endswith(":free") and not allow_paid:
            raise ValueError(
                f"O modelo '{model}' é pago. Defina OPENROUTER_ALLOW_PAID=true "
                "para permitir custo, ou use uma variante ':free'."
            )
        self._api_key = api_key
        self._model = model
        self._storage_dir = Path(storage_dir)
        self._timeout = timeout
        self._transport = transport
        self.name = f"openrouter:{model}"

    def generate(self, request: str, *, idempotency_key: str) -> ProviderImage:
        existing = self._find_stored(idempotency_key)
        if existing is not None:
            return ProviderImage(reference=self._reference(existing))

        payload = self._call_api(request)
        data, media_type = self._extract_image(payload)
        path = self._store(idempotency_key, data, media_type)
        return ProviderImage(
            reference=self._reference(path),
            request_id=payload.get("id"),
        )

    def _call_api(self, prompt: str) -> dict:
        headers = {
            "Authorization": f"Bearer {self._api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }
        body = {"model": self._model, "prompt": prompt, "aspect_ratio": "1:1"}
        try:
            with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
                response = client.post(OPENROUTER_IMAGES_URL, headers=headers, json=body)
        except httpx.HTTPError as exc:
            raise ImageProviderError(f"Falha de rede no OpenRouter: {type(exc).__name__}") from exc

        if response.status_code != 200:
            # O corpo do erro do OpenRouter não contém a chave; limita o tamanho.
            raise ImageProviderError(
                f"OpenRouter respondeu {response.status_code}: {response.text[:300]}"
            )
        try:
            return response.json()
        except ValueError as exc:
            raise ImageProviderError("Resposta do OpenRouter não é JSON.") from exc

    @staticmethod
    def _extract_image(payload: dict) -> tuple[bytes, str]:
        items = payload.get("data")
        if not isinstance(items, list) or not items:
            raise ImageProviderError("Resposta do OpenRouter sem imagem em `data`.")
        first = items[0]
        encoded = first.get("b64_json") if isinstance(first, dict) else None
        if not isinstance(encoded, str) or not encoded:
            raise ImageProviderError("Resposta do OpenRouter sem `b64_json`.")
        try:
            data = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ImageProviderError("Imagem em base64 inválida.") from exc
        media_type = first.get("media_type") or "image/png"
        return data, media_type

    def _store(self, key: str, data: bytes, media_type: str) -> Path:
        extension = EXTENSIONS.get(media_type, ".png")
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        target = self._storage_dir / f"{key}{extension}"
        fd, temp_name = tempfile.mkstemp(dir=self._storage_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
            os.replace(temp_name, target)
        except OSError as exc:
            Path(temp_name).unlink(missing_ok=True)
            raise ImageProviderError(f"Não foi possível gravar a imagem: {exc}") from exc
        return target

    def _find_stored(self, key: str) -> Path | None:
        for extension in EXTENSIONS.values():
            candidate = self._storage_dir / f"{key}{extension}"
            if candidate.is_file():
                return candidate
        return None

    @staticmethod
    def _reference(path: Path) -> str:
        """Referência estável `images/<arquivo>`, servida pela API em `/images/<arquivo>`."""
        return f"images/{path.name}"


def build_image_provider_from_env():
    """OpenRouter quando há OPENROUTER_API_KEY; caso contrário, o simulado."""
    from dotenv import load_dotenv

    from mcp_server.images import SimulatedImageProvider

    load_dotenv()
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        return SimulatedImageProvider()
    return OpenRouterImageProvider(
        SecretStr(key),
        model=os.getenv("OPENROUTER_IMAGE_MODEL", DEFAULT_IMAGE_MODEL).strip()
        or DEFAULT_IMAGE_MODEL,
        storage_dir=os.getenv("IMAGE_STORAGE_DIR", DEFAULT_STORAGE_DIR).strip()
        or DEFAULT_STORAGE_DIR,
        allow_paid=os.getenv("OPENROUTER_ALLOW_PAID", "").strip().lower() == "true",
    )
