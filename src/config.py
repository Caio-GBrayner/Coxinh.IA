import os

from dotenv import load_dotenv
from pydantic import BaseModel, SecretStr


class LLMConfig(BaseModel):
    """Define as configurações necessárias para chamar a LLM."""

    api_key: SecretStr
    model: str


class TavilyConfig(BaseModel):
    """Define a configuração necessária para pesquisar com o Tavily."""

    api_key: SecretStr


def load_llm_config() -> LLMConfig:
    """Carrega e valida as configurações da LLM."""

    load_dotenv()

    llm_key = os.getenv("LLM_KEY", "").strip()
    llm_model = os.getenv("LLM_MODEL", "").strip()

    if not llm_key:
        raise ValueError("LLM_KEY must be set.")

    if not llm_model:
        raise ValueError("LLM_MODEL must be set.")

    return LLMConfig(
        api_key=SecretStr(llm_key),
        model=llm_model,
    )


def load_tavily_config() -> TavilyConfig:
    """Carrega e valida a chave usada nas pesquisas do Tavily."""

    load_dotenv()

    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()

    if not tavily_key:
        raise ValueError("TAVILY_API_KEY must be set.")

    return TavilyConfig(
        api_key=SecretStr(tavily_key),
    )