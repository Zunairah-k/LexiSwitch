"""One call that runs the whole NLP pipeline: text -> tokens -> languages -> analysis."""
from dataclasses import asdict

from .analysis import analyze
from .config import LANGUAGES
from .model import OTHER, LanguageIdentifier


def language_name(code: str) -> str:
    return "Other" if code == OTHER else LANGUAGES.get(code, code)


def analyze_text(model: LanguageIdentifier, text: str) -> dict:
    preds = model.predict(text)
    tokens = []
    for p in preds:
        d = asdict(p)
        d["language_name"] = language_name(p.language)
        tokens.append(d)
    return {
        "text": text,
        "model_languages": [{"code": c, "name": language_name(c)} for c in model.classes],
        "tokens": tokens,
        "analysis": analyze(preds, len(model.classes)),
    }