"""Validação do texto do usuário: tamanho, regex e juiz LLM, nessa ordem.

Só um veredito `legitima` libera o texto. Dúvida, resposta inválida ou falha
técnica bloqueiam.
"""

import json
import logging
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.config import GuardConfig, load_guard_config
from src.graph.prompts.guard import GUARD_PROMPT
from src.utils.injection_patterns import (
    find_blocking_pattern,
    find_suspicions,
    normalize_text,
)
from src.utils.llm_adapter import create_chat_model, invoke_structured


logger = logging.getLogger(__name__)

GuardStage = Literal["request", "impasse"]
GuardCode = Literal[
    "allowed",
    "disabled",
    "prompt_injection",
    "guard_uncertain",
    "guard_unavailable",
    "input_too_long",
]

JUDGE_TEMPERATURE = 0.0
JUDGE_MAX_RETRIES = 1
MAX_REASON_CHARS = 240
REGEX_REASON = "O texto contém um padrão conhecido de manipulação dos agentes."

# Textos mostrados ao usuário na API, no terminal e no front.
MESSAGES: dict[str, str] = {
    "prompt_injection": (
        "Bloqueamos este texto porque ele parece uma tentativa de manipular os agentes."
    ),
    "guard_uncertain": (
        "Não conseguimos confirmar que este texto é seguro. Por precaução, ele não "
        "foi enviado ao Chef. Reescreva a ideia e tente de novo."
    ),
    "guard_unavailable": (
        "A verificação de segurança está indisponível. Por precaução, o texto não "
        "foi enviado ao Chef. Tente de novo em instantes."
    ),
    "input_too_long": "O texto é longo demais. Resuma e tente de novo.",
}


class JudgeVerdict(BaseModel):
    verdict: Literal["legitima", "manipulacao", "incerta"]
    reason: str = Field(description="One short sentence in Brazilian Portuguese.")


class GuardResult(BaseModel):
    code: GuardCode
    reason: str | None = None

    @property
    def allowed(self) -> bool:
        return self.code in ("allowed", "disabled")

    @property
    def message(self) -> str:
        """Mensagem completa para o usuário, com o motivo quando existe."""
        message = MESSAGES.get(self.code, "")
        return f"{message} Motivo: {self.reason}" if self.reason else message


class InputBlocked(ValueError):
    """O guardrail recusou um texto do usuário."""

    def __init__(self, result: GuardResult) -> None:
        super().__init__(result.message)
        self.result = result


def run_judge(
    text: str,
    stage: GuardStage,
    signals: list[str],
    config: GuardConfig,
) -> JudgeVerdict:
    """Pede ao modelo a intenção do texto. Qualquer falha sobe para quem chamou."""
    model = create_chat_model(
        config.llm,
        JUDGE_TEMPERATURE,
        timeout=config.timeout_seconds,
        max_retries=JUDGE_MAX_RETRIES,
    )
    # O texto vai como valor JSON: aspas e quebras são escapadas e ele não se
    # mistura com as instruções.
    context = json.dumps(
        {"stage": stage, "signals": signals, "user_text": text}, ensure_ascii=False
    )
    chain: Any = GUARD_PROMPT | model.with_structured_output(JudgeVerdict)
    return JudgeVerdict.model_validate(invoke_structured(chain, {"context": context}))


def check_text(text: str, stage: GuardStage) -> GuardResult:
    """Valida um texto do usuário. Nunca levanta exceção: falha vira bloqueio."""
    try:
        config = load_guard_config()
        if config is None:
            return GuardResult(code="disabled")
        if len(text) > config.max_input_chars:
            return GuardResult(code="input_too_long")

        normalized = normalize_text(text)
        pattern = find_blocking_pattern(normalized)
        if pattern is not None:
            logger.info("Guardrail blocked by pattern %s (%s).", pattern, stage)
            return GuardResult(code="prompt_injection", reason=REGEX_REASON)

        verdict = run_judge(text, stage, find_suspicions(normalized), config)
    except Exception as exc:
        logger.warning("Guardrail unavailable: %s", type(exc).__name__)
        return GuardResult(code="guard_unavailable")

    reason = " ".join(verdict.reason.split())[:MAX_REASON_CHARS] or None
    logger.info("Guardrail verdict %s (%s).", verdict.verdict, stage)
    if verdict.verdict == "legitima":
        return GuardResult(code="allowed")
    if verdict.verdict == "manipulacao":
        return GuardResult(code="prompt_injection", reason=reason)
    return GuardResult(code="guard_uncertain", reason=reason)
