import logging
from typing import Any

from groq import BadRequestError
from langchain_groq import ChatGroq

from src.config import load_llm_config


logger = logging.getLogger(__name__)

STRUCTURED_MAX_ATTEMPTS = 3


def call_llm(temperature: float) -> ChatGroq:
    config = load_llm_config()

    return ChatGroq(
        api_key=config.api_key,
        model=config.model,
        temperature=temperature,
    )


def invoke_structured(chain: Any, payload: dict[str, Any]) -> Any:
    """Chama uma cadeia de saída estruturada, repetindo se o modelo errar a ferramenta.

    O Groq responde 400 `tool_use_failed` quando o modelo não chama a ferramenta
    (resposta vazia ou recusa) ou a chama fora do esquema. Modelos menores erram
    isso de forma intermitente, e uma nova tentativa costuma resolver. Qualquer
    outro erro sobe na hora, sem retentativa.
    """
    last_error: BadRequestError | None = None

    for attempt in range(1, STRUCTURED_MAX_ATTEMPTS + 1):
        try:
            return chain.invoke(payload)
        except BadRequestError as exc:
            if "tool_use_failed" not in str(exc):
                raise
            last_error = exc
            logger.warning(
                "Structured output failed (attempt %s/%s).",
                attempt,
                STRUCTURED_MAX_ATTEMPTS,
            )

    assert last_error is not None
    raise last_error
