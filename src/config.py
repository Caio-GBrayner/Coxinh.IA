import os

from dotenv import load_dotenv
from pydantic import BaseModel, SecretStr


class LLMConfig(BaseModel):
    LLM_KEY: SecretStr
    LLM_MODEL: str


def load_llm_config() -> LLMConfig:
    load_dotenv()

    LLM_KEY = os.getenv("LLM_KEY", "").strip()
    LLM_MODEL = os.getenv("LLM_MODEL", "").strip()

    if not LLM_KEY:
        raise ValueError("A variável LLM_KEY precisa estar preenchida.")

    if not LLM_MODEL:
        raise ValueError("A variável LLM_MODEL precisa estar preenchida.")

    return LLMConfig(
        LLM_KEY=SecretStr(LLM_KEY),
        LLM_MODEL=LLM_MODEL,
    )