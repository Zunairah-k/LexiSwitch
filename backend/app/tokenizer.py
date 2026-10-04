"""Tokenizer: splits text into word tokens and keeps character offsets.

We split on whitespace and common punctuation, then strip punctuation/symbols
from the token edges. We do NOT use the regex \\w class because it breaks
Indic words at combining vowel signs (matras).
"""
import re
import unicodedata
from dataclasses import dataclass

_PIECE = re.compile(r"[^\s,;:/|()\[\]{}!?\"“”<>]+")


@dataclass
class Token:
    index: int
    text: str
    start: int
    end: int


def _junk(ch: str) -> bool:
    return unicodedata.category(ch)[0] in ("P", "S")  # punctuation or symbol


def tokenize(text: str) -> list[Token]:
    text = text.replace("’", "'").replace("‘", "'")  # same length: offsets stay valid
    tokens: list[Token] = []
    for m in _PIECE.finditer(text):
        piece, base = m.group(), m.start()
        lo, hi = 0, len(piece)
        while lo < hi and _junk(piece[lo]):
            lo += 1
        while hi > lo and _junk(piece[hi - 1]):
            hi -= 1
        if lo < hi:
            tokens.append(Token(len(tokens), piece[lo:hi], base + lo, base + hi))
    return tokens