"""Unicode script detection: which writing system is this token written in?"""
import unicodedata
from collections import Counter


def detect_script(word: str) -> str:
    """Return the dominant Unicode script name (e.g. 'LATIN', 'TELUGU'),
    or 'NONE' if the token has no letters (numbers, symbols)."""
    counts: Counter[str] = Counter()
    for ch in word:
        if unicodedata.category(ch)[0] in ("L", "M"):  # letters and combining marks
            name = unicodedata.name(ch, "")
            if name:
                counts[name.split(" ")[0]] += 1
    return counts.most_common(1)[0][0] if counts else "NONE"