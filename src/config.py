import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr


class LLMConfig(BaseModel):
    """Define as configurações necessárias para chamar a LLM."""

    api_key: SecretStr
    model: str
    provider: str = "groq"


class GuardConfig(BaseModel):
    """Define o juiz e os limites do guardrail de entrada."""

    llm: LLMConfig
    max_input_chars: int = Field(gt=0)
    timeout_seconds: float = Field(gt=0)


class TavilyConfig(BaseModel):
    """Define a configuração necessária para pesquisar com o Tavily."""

    api_key: SecretStr


def load_llm_config() -> LLMConfig:
    """Carrega e valida as configurações da LLM."""

    load_dotenv()

    return _llm_config(
        os.getenv("LLM_PROVIDER", "groq").strip().lower(),
        os.getenv("LLM_MODEL", "").strip(),
    )


def load_guard_config() -> GuardConfig | None:
    """Carrega o guardrail; None quando ele foi desligado de propósito."""

    load_dotenv()

    # Só um "não" explícito desliga: um valor digitado errado mantém a proteção.
    if os.getenv("GUARD_ENABLED", "").strip().lower() in ("false", "0", "no", "off"):
        return None

    main_provider = os.getenv("LLM_PROVIDER", "groq").strip().lower()
    provider = os.getenv("GUARD_JUDGE_PROVIDER", "").strip().lower() or main_provider
    model = os.getenv("GUARD_JUDGE_MODEL", "").strip()
    if not model and provider != main_provider:
        raise ValueError("GUARD_JUDGE_MODEL must be set when the judge uses another provider.")

    return GuardConfig(
        llm=_llm_config(provider, model or os.getenv("LLM_MODEL", "").strip()),
        max_input_chars=int(os.getenv("GUARD_MAX_INPUT_CHARS", "").strip() or 4000),
        timeout_seconds=float(
            os.getenv("GUARD_JUDGE_TIMEOUT_SECONDS", "").strip() or 15
        ),
    )


def _llm_config(llm_provider: str, llm_model: str) -> LLMConfig:
    if llm_provider == "google":
        key_variable = "GOOGLE_API_KEY"
        llm_key = os.getenv(key_variable, "").strip()
    elif llm_provider == "groq":
        key_variable = "LLM_KEY"
        llm_key = os.getenv(key_variable, "").strip()
    else:
        raise ValueError("LLM_PROVIDER must be 'google' or 'groq'.")

    if not llm_key:
        raise ValueError(f"{key_variable} must be set.")

    if not llm_model:
        raise ValueError("LLM_MODEL must be set.")

    return LLMConfig(
        api_key=SecretStr(llm_key),
        model=llm_model,
        provider=llm_provider,
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
