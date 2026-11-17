import os

from dotenv import load_dotenv
from pydantic import BaseModel, SecretStr


class LLMConfig(BaseModel):
    api_key: SecretStr
    model: str


def load_llm_config() -> LLMConfig:
    load_dotenv()

    LLM_KEY = os.getenv("LLM_KEY", "").strip()
    LLM_MODEL = os.getenv("LLM_MODEL", "").strip()

    if not LLM_KEY:
        raise ValueError("LLM_KEY must be set.")

    if not LLM_MODEL:
        raise ValueError("LLM_MODEL must be set.")

    return LLMConfig(
        api_key=SecretStr(LLM_KEY),
        model=LLM_MODEL,
    )