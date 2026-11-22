import re
from html import unescape

from pydantic import BaseModel, HttpUrl, ValidationError
from tavily import TavilyClient

from src.config import load_tavily_config
from src.schemas import NonEmptyText


MAX_RESULTS = 3
MAX_CONTENT_LENGTH = 500
SEARCH_TIMEOUT = 20


class WebSearchResult(BaseModel):
    """Valida o título, a URL e o trecho de uma fonte encontrada."""

    title: NonEmptyText
    url: HttpUrl
    content: NonEmptyText


def clean_content(content: str) -> str:
    """Remove tags HTML, normaliza espaços e limita o tamanho do trecho."""

    text = re.sub(r"<[^>]+>", " ", content)
    text = unescape(text)
    text = " ".join(text.split())

    return text[:MAX_CONTENT_LENGTH]


def search_web(query: str) -> list[dict[str, str]]:
    """Pesquisa no Tavily e devolve as fontes válidas para o agente."""

    query = query.strip()

    if not query:
        raise ValueError("A consulta de pesquisa precisa estar preenchida.")

    config = load_tavily_config()
    client = TavilyClient(api_key=config.api_key.get_secret_value())

    response = client.search(
        query=query,
        search_depth="basic",
        max_results=MAX_RESULTS,
        include_answer=False,
        include_raw_content=False,
        include_images=False,
        auto_parameters=False,
        timeout=SEARCH_TIMEOUT,
    )

    results = []

    for item in response["results"][:MAX_RESULTS]:
        try:
            source = WebSearchResult.model_validate(item)
            source.content = clean_content(source.content)

            if not source.content:
                continue

            results.append(source.model_dump(mode="json"))
        except ValidationError:
            continue

    return results