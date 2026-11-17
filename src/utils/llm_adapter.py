from langchain_groq import ChatGroq

from src.config import load_llm_config


def call_llm(temperature: float) -> ChatGroq:
    config = load_llm_config()

    return ChatGroq(
        api_key=config.LLM_KEY.get_secret_value(),
        model=config.LLM_MODEL,
        temperature=temperature,
    )