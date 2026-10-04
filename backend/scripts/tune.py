"""Tunes the two context settings on the DEV set only and saves them.
Usage (from backend/): python scripts\\tune.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from evaluate import evaluate, load_gold, switch_summary, token_metrics  # noqa: E402
from app.config import PARAMS_PATH  # noqa: E402
from app.model import OTHER, LanguageIdentifier  # noqa: E402

DEV = ROOT / "data" / "eval" / "dev.txt"
S_GRID = [None, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
L_GRID = [0.7, 0.8, 0.9, 0.95]

model = LanguageIdentifier.load()
sentences, problems = load_gold(DEV, set(model.classes) | {OTHER})
if problems:
    sys.exit("Fix dev.txt first:\n" + "\n".join(problems))

print(f"{'switch_prior':>13}{'lexicon_conf':>14}{'accuracy':>10}{'macro-F1':>10}{'switch F1':>11}")
best, best_key = None, None
for s in S_GRID:
    for lam in L_GRID:
        model.switch_prior, model.lexicon_conf = s, lam
        res = evaluate(model, sentences)
        _, _, _, acc, macro, _ = token_metrics(res["rows"], model.classes)
        swf = switch_summary(res["pairs"])["f1"] or 0.0
        print(f"{str(s):>13}{lam:>14}{acc:>10.3f}{macro:>10.3f}{swf:>11.3f}")
        key = (round(macro, 4), round(swf, 4))
        if best_key is None or key > best_key:      # ties keep the earlier (simpler) setting
            best, best_key = (s, lam), key

s, lam = best
if s is None:
    lam = 0.9
PARAMS_PATH.write_text(json.dumps(
    {"switch_prior": s, "lexicon_confidence": lam, "tuned_on": "data/eval/dev.txt"}, indent=2),
    encoding="utf-8")
print(f"\nBest on dev: switch_prior={s}, lexicon_confidence={lam}  -> saved to {PARAMS_PATH}")