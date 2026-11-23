from concurrent.futures import ThreadPoolExecutor
import re
import time

import pytest

from mcp_server.images import (
    PROMPT_VERSION,
    ImageProviderError,
    ImageService,
    ProviderImage,
    SimulatedImageProvider,
    build_idempotency_key,
    build_image_request,
)
from src.schemas import Recipe


IMAGE_PROMPT = "Coxinha dourada com recheio de frango."


def create_recipe(**overrides) -> Recipe:
    values = {
        "dough": "Potato dough",
        "filling": "Chicken",
        "ingredients": ["potato", "chicken"],
        "preparation": "Boil the potatoes and shape the dough.",
        "utensils": ["pot"],
        "preparation_methods": ["boiling", "frying"],
    }
    values.update(overrides)
    return Recipe(**values)


def key_for(recipe: Recipe, prompt: str = IMAGE_PROMPT, **kwargs) -> str:
    kwargs.setdefault("provider_name", "simulated")
    return build_idempotency_key(recipe, prompt, **kwargs)


class SlowProvider:
    """Provedor lento para expor corridas entre chamadas simultâneas."""

    name = "slow"

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, request: str, *, idempotency_key: str) -> ProviderImage:
        self.calls += 1
        time.sleep(0.05)
        return ProviderImage(reference="slow://image", request_id="slow-1")


class FlakyProvider:
    """Falha na primeira chamada e funciona nas seguintes."""

    name = "flaky"

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, request: str, *, idempotency_key: str) -> ProviderImage:
        self.calls += 1
        if self.calls == 1:
            raise ImageProviderError("provider down")
        return ProviderImage(reference="flaky://image")


def test_key_is_a_stable_sha256_hex_digest():
    key = key_for(create_recipe())

    assert key == key_for(create_recipe())
    assert re.fullmatch(r"[0-9a-f]{64}", key)


def test_key_ignores_whitespace_and_list_order():
    original = create_recipe()
    reshuffled = create_recipe(
        dough="  Potato   dough ",
        ingredients=["chicken", "potato"],
        preparation_methods=["frying", "boiling"],
    )

    assert key_for(original) == key_for(reshuffled)


@pytest.mark.parametrize(
    "recipe",
    [
        create_recipe(filling="Cheese"),
        create_recipe(dough="Cassava dough"),
        create_recipe(ingredients=["potato", "chicken", "olive"]),
        create_recipe(preparation_methods=["baking"]),
    ],
)
def test_key_changes_when_the_recipe_changes(recipe):
    assert key_for(recipe) != key_for(create_recipe())


def test_key_changes_with_prompt_provider_and_version():
    recipe = create_recipe()
    base = key_for(recipe)

    assert key_for(recipe, "Outra descrição.") != base
    assert key_for(recipe, provider_name="other") != base
    assert key_for(recipe, prompt_version="v2") != base


def test_key_ignores_fields_that_do_not_change_the_image():
    # Os utensílios e o texto de preparo não entram na chave.
    changed = create_recipe(utensils=["frigideira"], preparation="Outro texto.")

    assert key_for(changed) == key_for(create_recipe())


def test_image_request_is_faithful_to_the_recipe_and_not_a_real_photo():
    request = build_image_request(create_recipe(), IMAGE_PROMPT)

    assert IMAGE_PROMPT in request
    assert "Massa: Potato dough" in request
    assert "Recheio: Chicken" in request
    assert "potato, chicken" in request
    assert "boiling, frying" in request
    assert "coxinha fictícia" in request
    assert "fotografia realista" in request


def test_generate_then_reuse_calls_the_provider_once():
    provider = SimulatedImageProvider()
    service = ImageService(provider)

    first = service.generate(create_recipe(), IMAGE_PROMPT)
    second = service.generate(create_recipe(), IMAGE_PROMPT)

    assert first.status == "generated"
    assert second.status == "reused"
    assert second.image_reference == first.image_reference
    assert second.idempotency_key == first.idempotency_key
    assert provider.calls == 1


def test_a_different_recipe_generates_a_new_image():
    provider = SimulatedImageProvider()
    service = ImageService(provider)

    first = service.generate(create_recipe(), IMAGE_PROMPT)
    second = service.generate(create_recipe(filling="Cheese"), IMAGE_PROMPT)

    assert second.status == "generated"
    assert second.image_reference != first.image_reference
    assert provider.calls == 2


def test_concurrent_calls_with_the_same_key_generate_once():
    provider = SlowProvider()
    service = ImageService(provider)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(
            pool.map(
                lambda _: service.generate(create_recipe(), IMAGE_PROMPT),
                range(8),
            )
        )

    statuses = sorted(result.status for result in results)
    assert statuses == ["generated"] + ["reused"] * 7
    assert provider.calls == 1


def test_provider_failure_is_not_stored_and_can_be_retried():
    provider = FlakyProvider()
    service = ImageService(provider)

    with pytest.raises(ImageProviderError):
        service.generate(create_recipe(), IMAGE_PROMPT)
    retry = service.generate(create_recipe(), IMAGE_PROMPT)

    assert retry.status == "generated"
    assert provider.calls == 2


def test_default_prompt_version_is_part_of_the_contract():
    assert PROMPT_VERSION == "v1"
