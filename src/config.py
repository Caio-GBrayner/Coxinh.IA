import os

from dotenv import load_dotenv
from pydantic import BaseModel, SecretStr


class LLMConfig(BaseModel):
    api_key: SecretStr
    model: str


def load_llm_config() -> LLMConfig:
    load_dotenv()

    api_key = os.getenv("LLM_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()

    if not api_key:
        raise ValueError("A variável LLM_KEY precisa estar preenchida.")

    if not model:
        raise ValueError("A variável LLM_MODEL precisa estar preenchida.")

    return LLMConfig(
        api_key=SecretStr(api_key),
        model=model,
    )