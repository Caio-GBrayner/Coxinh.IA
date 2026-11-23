"""Texto livre de ingredientes: separar itens e comparar de forma tolerante.

As pessoas digitam do jeito que acham natural ("queijo, carne e fogão",
"- pão\n- manteiga"). Estas funções transformam esse texto em itens e comparam
itens sem depender de acentos, maiúsculas, espaços ou de o nome estar completo.
"""

import re
import unicodedata


# Vírgula, ponto e vírgula, quebra de linha, barra e o conectivo "e"/"and"
# isolado por espaços separam itens.
_SEPARATORS = re.compile(r"[,;\n\r/|]+|\s+(?:e|and|&)\s+", re.IGNORECASE)
# Marcadores de lista no começo do item: "-", "*", "•", "1.", "2)".
_LIST_MARKER = re.compile(r"^\s*(?:[-*•·]+|\d+[.)])\s*")


def split_items(values: str | list[str] | None) -> list[str]:
    """Separa texto livre em itens limpos, sem repetidos, mantendo a ordem."""
    if values is None:
        return []
    texts = [values] if isinstance(values, str) else list(values)

    items: list[str] = []
    seen: set[str] = set()
    for text in texts:
        if not isinstance(text, str):
            continue
        for part in _SEPARATORS.split(text):
            item = _LIST_MARKER.sub("", part).strip(" \t.\"'")
            item = " ".join(item.split())
            key = normalize_for_match(item)
            if item and key not in seen:
                seen.add(key)
                items.append(item)
    return items


def normalize_for_match(text: str) -> str:
    """Minúsculas, sem acentos e com espaços simples: 'Pão  Francês' -> 'pao frances'."""
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(without_accents.casefold().split())


def mentions(item: str, candidate: str) -> bool:
    """Diz se `item` aparece em `candidate` como palavras inteiras, ou o contrário.

    'queijo' aparece em 'queijo ralado'; 'pao' casa com 'pão'; 'carne moida'
    casa com 'carne'. Trechos de palavra não contam: 'sal' não casa com 'salsa'.
    """
    item_words = normalize_for_match(item).split()
    candidate_words = normalize_for_match(candidate).split()
    if not item_words or not candidate_words:
        return False
    return _contains(candidate_words, item_words) or _contains(item_words, candidate_words)


def _contains(words: list[str], part: list[str]) -> bool:
    size = len(part)
    return any(words[index : index + size] == part for index in range(len(words) - size + 1))
