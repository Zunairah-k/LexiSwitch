import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "train_words.csv"
MODEL_DIR = ROOT / "models"

# Every language we have training data for.
LANGUAGES = {
    "en": "English", "bn": "Bengali", "gu": "Gujarati", "hi": "Hindi",
    "kn": "Kannada", "ml": "Malayalam", "mr": "Marathi", "pa": "Punjabi",
    "sd": "Sindhi", "si": "Sinhala", "ta": "Tamil", "te": "Telugu", "ur": "Urdu",
}
INDIC_CODES = [c for c in LANGUAGES if c != "en"]

# The languages the system actually identifies. The classifier chooses
# only among these. Add a code here and retrain to extend the system.
ACTIVE_LANGUAGES = ["en", "hi", "te"]


def model_path(langs=None):
    langs = sorted(langs or ACTIVE_LANGUAGES)
    return MODEL_DIR / f"langid_{'-'.join(langs)}.joblib"


MAX_WORDS_PER_LANG = 20000   # per language, per script form
NGRAM_RANGE = (1, 4)         # character n-gram sizes
ALPHA = 0.1                  # Naive Bayes smoothing

# Which languages can a script belong to? (Unicode script -> candidates)
SCRIPT_LANGS = {
    "LATIN": list(LANGUAGES),        # romanized text: any language, incl. English
    "DEVANAGARI": ["hi", "mr"],
    "ARABIC": ["ur", "sd"],
    "BENGALI": ["bn"],
    "GUJARATI": ["gu"],
    "GURMUKHI": ["pa"],
    "KANNADA": ["kn"],
    "MALAYALAM": ["ml"],
    "SINHALA": ["si"],
    "TAMIL": ["ta"],
    "TELUGU": ["te"],
}

# Context-smoothing settings, written by scripts/tune.py (dev set only).
PARAMS_PATH = ROOT / "app" / "tuned_params.json"
DEFAULT_PARAMS = {"switch_prior": None, "lexicon_confidence": 0.9, "bias_scale": 1.0}


def load_params() -> dict:
    if PARAMS_PATH.exists():
        return {**DEFAULT_PARAMS, **json.loads(PARAMS_PATH.read_text(encoding="utf-8"))}
    return dict(DEFAULT_PARAMS)