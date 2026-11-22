import hashlib
import json
from threading import Lock
from typing import Literal, Protocol
import unicodedata

from pydantic import BaseModel

from src.schemas import Recipe


PROMPT_VERSION = "v1"


class ImageProviderError(RuntimeError):
    """Falha do provedor de imagem (rede, autenticação, cota ou tempo esgotado)."""


class ProviderImage(BaseModel, frozen=True):
    reference: str
    request_id: str | None = None


class ImageProvider(Protocol):
    name: str

    def generate(self, request: str, *, idempotency_key: str) -> ProviderImage:
        """Gera uma imagem. Levanta ImageProviderError em falhas externas."""


class SimulatedImageProvider:
    """Provedor simulado. Não acessa rede nem gera custo.

    O provedor real depende da decisão 12 do plano.
    """

    name = "simulated"

    def __init__(self) -> None:
        self.calls = 0
        self._lock = Lock()

    def generate(self, request: str, *, idempotency_key: str) -> ProviderImage:
        with self._lock:
            self.calls += 1
            number = self.calls
        return ProviderImage(
            reference=f"simulated://coxinha/{idempotency_key[:16]}",
            request_id=f"simulated-{number}",
        )


class GeneratedImage(BaseModel, frozen=True):
    status: Literal["generated", "reused"]
    image_reference: str
    idempotency_key: str
    provider_request_id: str | None = None


def _clean(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).split())


def canonical_image_input(
    recipe: Recipe,
    image_prompt: str,
    *,
    prompt_version: str,
    provider_name: str,
) -> dict[str, object]:
    """Entrada canônica da chave. Título e subtítulo ficam de fora."""
    return {
        "dough": _clean(recipe.dough),
        "filling": _clean(recipe.filling),
        "ingredients": sorted(_clean(item) for item in recipe.ingredients),
        "preparation_methods": sorted(
            _clean(item) for item in recipe.preparation_methods
        ),
        "image_prompt": _clean(image_prompt),
        "prompt_version": _clean(prompt_version),
        "provider": provider_name,
    }


def build_idempotency_key(
    recipe: Recipe,
    image_prompt: str,
    *,
    prompt_version: str = PROMPT_VERSION,
    provider_name: str,
) -> str:
    """SHA-256 da entrada canônica. Nenhum valor aleatório entra na chave."""
    canonical = canonical_image_input(
        recipe,
        image_prompt,
        prompt_version=prompt_version,
        provider_name=provider_name,
    )
    encoded = json.dumps(
        canonical, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_image_request(recipe: Recipe, image_prompt: str) -> str:
    """Pedido ao provedor, fiel à receita final e sem apresentá-la como real."""
    return (
        "Crie uma imagem ilustrativa e fictícia de uma coxinha baseada nesta "
        f"descrição:\n{_clean(image_prompt)}\n\n"
        f"Massa: {_clean(recipe.dough)}\n"
        f"Recheio: {_clean(recipe.filling)}\n"
        f"Ingredientes: {', '.join(_clean(item) for item in recipe.ingredients)}\n"
        "Métodos de preparo: "
        f"{', '.join(_clean(item) for item in recipe.preparation_methods)}\n\n"
        "Não apresente a imagem como fotografia de um alimento real ou seguro "
        "para consumo."
    )


class ImageService:
    """Gera imagens com reutilização por chave de idempotência.

    Garantias (MVP, índice em memória):
    - mesma chave no mesmo processo reutiliza o resultado;
    - chamadas simultâneas com a mesma chave geram uma única vez;
    - reinício ou vários processos perdem o índice, e a imagem pode ser gerada
      de novo;
    - se o provedor responder e o processo cair antes de gravar o resultado, a
      imagem pode ser gerada de novo. A chave sozinha não evita esse caso.
    """

    def __init__(self, provider: ImageProvider) -> None:
        self._provider = provider
        self._results: dict[str, ProviderImage] = {}
        self._locks: dict[str, Lock] = {}
        self._guard = Lock()

    def generate(
        self,
        recipe: Recipe,
        image_prompt: str,
        *,
        prompt_version: str = PROMPT_VERSION,
    ) -> GeneratedImage:
        key = build_idempotency_key(
            recipe,
            image_prompt,
            prompt_version=prompt_version,
            provider_name=self._provider.name,
        )
        with self._key_lock(key):
            stored = self._results.get(key)
            if stored is not None:
                return GeneratedImage(
                    status="reused",
                    image_reference=stored.reference,
                    idempotency_key=key,
                    provider_request_id=stored.request_id,
                )

            produced = self._provider.generate(
                build_image_request(recipe, image_prompt),
                idempotency_key=key,
            )
            self._results[key] = produced
            return GeneratedImage(
                status="generated",
                image_reference=produced.reference,
                idempotency_key=key,
                provider_request_id=produced.request_id,
            )

    def _key_lock(self, key: str) -> Lock:
        with self._guard:
            if key not in self._locks:
                self._locks[key] = Lock()
            return self._locks[key]
