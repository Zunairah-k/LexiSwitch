"""Run the full pipeline: python scripts\\try_analysis.py ["sentence" ...] [--langs en,hi,te]"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from app.model import LanguageIdentifier  # noqa: E402
from app.pipeline import analyze_text, language_name  # noqa: E402

DEFAULTS = [
    "Nenu assignment submit chesanu but mam asked for corrections.",
    "I submitted my assignment yesterday.",
    "Nenu kal office mein meeting attend cheyyali but I'm not sure.",
    "నేను assignment submit చేశాను",
]

ap = argparse.ArgumentParser()
ap.add_argument("texts", nargs="*")
ap.add_argument("--langs", default=None)
args = ap.parse_args()

model = LanguageIdentifier.load(args.langs.split(",") if args.langs else None)
for text in args.texts or DEFAULTS:
    r = analyze_text(model, text)
    a = r["analysis"]
    print(f"\n{text}")
    print("  tokens :", " ".join(f"{t['text']}/{t['language']}" for t in r["tokens"]))
    print("  flow   :", " -> ".join(language_name(l) for l in a["sequence"]) or "-")
    for s in a["switches"]:
        print(f"  switch : {s['from_language']} -> {s['to_language']} "
              f"at position {s['position']}")
    print("  dist   :", ", ".join(f"{d['language']} {d['tokens']} ({d['proportion']:.0%})"
                                  for d in a["distribution"]))
    print(f"  tokens analysed {a['tokens_analyzed']}/{a['tokens_total']}, "
          f"switches {a['switch_count']}, languages {a['language_count']}")
    dens = "n/a" if a["switch_density"] is None else f"{a['switch_density']:.3f}"
    mix = "n/a" if a["mixing_index"] is None else f"{a['mixing_index']:.3f}"
    print(f"  dominant {a['dominant_languages']}, density {dens}, mixing {mix}, "
          f"scripts {a['scripts']}")
    for u in a["uncertain_tokens"][:3]:
        print(f"  unsure : {u['token']} {u['language']} {u['probability']:.2f} "
              f"vs {u['runner_up']} {u['runner_up_probability']:.2f}")