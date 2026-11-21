import logging
from typing import Any, Self

from pydantic import BaseModel, Field, model_validator

from src.graph.health_search import (
    HealthSearch,
    build_health_queries,
    simulated_health_search,
)
from src.graph.prompts.health import HEALTH_PROMPT
from src.schemas import NonEmptyText, Recipe
from src.state import RecipeState
from src.utils.llm_adapter import call_llm


logger = logging.getLogger(__name__)

HEALTH_TEMPERATURE = 0.3
UNAVAILABLE_MESSAGE = "Não foi possível consultar o aviso de saúde."
NO_EVIDENCE_MESSAGE = "Não há informação suficiente nas fontes consultadas."
HEALTH_SEARCH: HealthSearch = simulated_health_search


class HealthSource(BaseModel):
    title: NonEmptyText
    url: NonEmptyText | None = None


class HealthAdvice(BaseModel):
    health_warning: NonEmptyText
    contraindications: list[NonEmptyText] = Field(default_factory=list)
    possible_effects: list[NonEmptyText] = Field(default_factory=list)
    sources_used: list[HealthSource] = Field(default_factory=list)
    uncertainty: NonEmptyText | None = None

    @model_validator(mode="after")
    def require_uncertainty_without_sources(self) -> Self:
        if not self.sources_used and not self.uncertainty:
            raise ValueError("Advice without sources must declare its uncertainty.")
        return self


class HealthContext(BaseModel):
    recipe: Recipe
    retrieved_health_context: list[dict[str, Any]]


def _normalize(value: str) -> str:
    return " ".join(value.split()).casefold()


def _index_known_sources(
    retrieved: list[dict[str, Any]],
) -> dict[tuple[str, str], HealthSource]:
    """Indexa as fontes recuperadas por URL e por título."""
    index: dict[tuple[str, str], HealthSource] = {}
    for item in retrieved:
        title = item.get("title")
        url = item.get("url")
        if not isinstance(title, str) or not title.strip():
            continue
        source = HealthSource(
            title=title,
            url=url if isinstance(url, str) and url.strip() else None,
        )
        if source.url is not None:
            index.setdefault(("url", _normalize(source.url)), source)
        index.setdefault(("title", _normalize(source.title)), source)
    return index


def _filter_used_sources(
    cited: list[HealthSource],
    retrieved: list[dict[str, Any]],
) -> list[HealthSource]:
    """Mantém apenas fontes citadas que existem no contexto recuperado."""
    index = _index_known_sources(retrieved)
    used: list[HealthSource] = []
    for source in cited:
        key = (
            ("url", _normalize(source.url))
            if source.url is not None
            else ("title", _normalize(source.title))
        )
        known = index.get(key)
        if known is not None and known not in used:
            used.append(known)
    return used


def _retrieve(recipe: Recipe) -> list[dict[str, Any]]:
    """Executa as três consultas da etapa 8 (massa, recheio e preparo)."""
    results: list[dict[str, Any]] = []
    for query in build_health_queries(recipe):
        results.extend(HEALTH_SEARCH(query))
    return results


def health_node(state: RecipeState) -> dict[str, Any]:
    recipe_value = state.get("recipe")
    if recipe_value is None:
        raise ValueError("The health node requires a recipe to advise on.")

    recipe = Recipe.model_validate(recipe_value)

    try:
        context = HealthContext(
            recipe=recipe,
            retrieved_health_context=_retrieve(recipe),
        )
        structured_model = HEALTH_PROMPT | call_llm(
            HEALTH_TEMPERATURE
        ).with_structured_output(HealthAdvice)
        advice = HealthAdvice.model_validate(
            structured_model.invoke({"context": context.model_dump_json()})
        )
    except Exception as exc:
        logger.warning("Health advice unavailable: %s", type(exc).__name__)
        return {
            "health_status": "unavailable",
            "health_warning": None,
            "contraindications": None,
            "health_sources": [],
            "health_uncertainty": UNAVAILABLE_MESSAGE,
        }

    sources = _filter_used_sources(
        advice.sources_used, context.retrieved_health_context
    )
    uncertainty = advice.uncertainty
    if not sources and uncertainty is None:
        uncertainty = NO_EVIDENCE_MESSAGE

    return {
        "health_status": "ok",
        "health_warning": advice.health_warning,
        "contraindications": list(advice.contraindications),
        "health_sources": [source.model_dump() for source in sources],
        "health_uncertainty": uncertainty,
    }
