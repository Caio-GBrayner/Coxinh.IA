"""Padrões de prompt injection verificados antes de qualquer chamada ao modelo.

- BLOCK_PATTERNS: frases inequívocas. Uma ocorrência bloqueia direto.
- SUSPICION_PATTERNS: frases que também aparecem em receitas legítimas. Não
  bloqueiam; o nome do padrão vai para o juiz como sinal.

Os padrões são comparados com o texto já normalizado por `normalize_text`
(minúsculas, sem acentos e com espaços simples). Use só quantificadores
limitados (`.{0,40}`), para o tempo da busca não explodir.
"""

import re
import unicodedata


_OVERRIDE = (
    r"\b(?:ignor\w{1,4}|desconsider\w{1,4}|esquec\w{1,3}|disregard|forget|override)\b"
)
_REVEAL = (
    r"\b(?:revel\w{1,4}|mostr\w{1,4}|imprim\w{1,3}|repit\w{1,3}|exib\w{1,3}|"
    r"reveal|show|print|repeat|leak|output)\b"
)
_INSTRUCTIONS = r"(?:instruc\w{2,5}|instructions?|regras|rules|prompts?|ordens|orders)"

BLOCK_PATTERNS: dict[str, re.Pattern[str]] = {
    "ignorar_instrucoes": re.compile(
        _OVERRIDE
        + r".{0,40}\b(?:"
        + _INSTRUCTIONS
        + r" (?:anteriores|previas|acima|iniciais|do sistema|above)"
        + r"|(?:previous|prior|above|earlier|system) (?:\w{1,12} )?"
        + _INSTRUCTIONS
        + r")\b"
    ),
    "revelar_prompt": re.compile(
        _REVEAL
        + r".{0,40}\b(?:system prompt|prompt (?:do|de) sistema|"
        + r"(?:hidden|internal|system) instructions|"
        + r"instrucoes (?:internas|ocultas|secretas|do sistema))\b"
    ),
    "marcador_de_papel": re.compile(
        r"<\|(?:im_start|im_end|system|user|assistant|endoftext|eot_id|"
        r"begin_of_text|start_header_id|end_header_id)\|>"
        r"|\[/?inst\]|<</?sys>>|<(?:start|end)_of_turn>"
    ),
    "modo_sem_regras": re.compile(
        r"\bdo anything now\b"
        r"|\bdeveloper mode (?:enabled|on|activated)\b"
        r"|\bmodo (?:desenvolvedor|developer) (?:ativado|ligado)\b"
    ),
}

SUSPICION_PATTERNS: dict[str, re.Pattern[str]] = {
    "ignorar_algo": re.compile(_OVERRIDE + r".{0,40}\b" + _INSTRUCTIONS + r"\b"),
    "troca_de_papel": re.compile(
        r"\b(?:voce agora e|a partir de agora voce|aja como|finja (?:que|ser)|"
        r"you are now|from now on you|act as|pretend (?:to be|you))\b"
    ),
    "instrucoes_do_agente": re.compile(
        r"\b(?:suas (?:instrucoes|regras)|your (?:instructions|rules|prompt)|"
        r"prompt|jailbreak)\b"
    ),
    "fala_de_sistema": re.compile(
        r"\b(?:system|assistant|developer|sistema|assistente)\s?:"
    ),
    "segredos": re.compile(
        r"\b(?:api[ _-]?key|chaves? (?:de|da) api|senhas?|passwords?|"
        r"variave(?:l|is) de ambiente|environment variables?)\b|\.env\b"
    ),
    "comando_ao_avaliador": re.compile(
        r"\b(?:classifi\w{1,5}|respond\w{0,3}|retorn\w{1,3}|return|marque|mark)\b"
        r".{0,40}\b(?:legitim\w{1,4}|aprovad\w|approved)\b"
        r"|\baprov\w{1,4} (?:sem (?:revis|avali|verific)\w{1,6}|automaticamente)\b"
    ),
    "bloco_codificado": re.compile(r"[a-z0-9+/]{60,}={0,2}"),
}


def normalize_text(text: str) -> str:
    """Desfaz disfarces comuns: maiúsculas, acentos, letras largas e caracteres invisíveis."""
    decomposed = unicodedata.normalize("NFKD", unicodedata.normalize("NFKC", text).casefold())
    visible = "".join(
        char
        for char in decomposed
        if unicodedata.category(char) not in ("Cf", "Mn", "Me")
    )
    spaced = "".join(
        " " if unicodedata.category(char) == "Cc" else char for char in visible
    )
    return " ".join(spaced.split())


def find_blocking_pattern(normalized: str) -> str | None:
    """Nome do primeiro padrão inequívoco encontrado, ou None."""
    return next(
        (name for name, pattern in BLOCK_PATTERNS.items() if pattern.search(normalized)),
        None,
    )


def find_suspicions(normalized: str) -> list[str]:
    """Nomes dos padrões ambíguos encontrados, para o juiz considerar."""
    return [
        name for name, pattern in SUSPICION_PATTERNS.items() if pattern.search(normalized)
    ]
