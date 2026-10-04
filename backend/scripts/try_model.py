"""Quick check: python scripts\\try_model.py ["sentence" ...] [--langs en,hi,te]"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from app.model import LanguageIdentifier  # noqa: E402

DEFAULTS = [
    "Nenu assignment submit chesanu but mam asked for corrections.",
    "నేను assignment submit చేశాను",
    "Kal office mein meeting hai but I'm not sure.",
]

ap = argparse.ArgumentParser()
ap.add_argument("texts", nargs="*")
ap.add_argument("--langs", default=None)
args = ap.parse_args()

model = LanguageIdentifier.load(args.langs.split(",") if args.langs else None)
for text in args.texts or DEFAULTS:
    print(f"\n{text}")
    for p in model.predict(text):
        prob = f"{p.probability:.3f}" if p.probability is not None else "-"
        print(f"  {p.index:>2}  {p.text:<16}{p.script:<11}{p.language:<7}{p.method:<24}{prob}")