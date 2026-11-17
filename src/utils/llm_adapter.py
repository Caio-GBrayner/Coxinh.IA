from langchain_groq import ChatGroq

from src.config import load_llm_config


def call_llm(temperature: float) -> ChatGroq:
    config = load_llm_config()

    return ChatGroq(
        api_key=config.api_key,
        model=config.model,
        temperature=temperature,
    )