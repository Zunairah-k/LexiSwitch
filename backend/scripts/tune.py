"""Tunes the context and bias settings on the DEV set only and saves them.
Smoothing is adopted only if it gains at least MIN_GAIN macro-F1.
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
B_GRID = [1.0, 0.75, 0.5, 0.25, 0.0]
S_GRID = [0.6, 0.5, 0.4, 0.3]
L_GRID = [0.8, 0.9, 0.95]
MIN_GAIN = 0.01

model = LanguageIdentifier.load()
sentences, problems = load_gold(DEV, set(model.classes) | {OTHER})
if problems:
    sys.exit("Fix dev.txt first:\n" + "\n".join(problems))


def score():
    res = evaluate(model, sentences)
    _, _, _, acc, macro, _ = token_metrics(res["rows"], model.classes)
    return acc, macro, switch_summary(res["pairs"])["f1"] or 0.0


print("Stage 1: bias scale (no smoothing)")
print(f"{'bias_scale':>11}{'accuracy':>10}{'macro-F1':>10}{'switch F1':>11}")
model.switch_prior = None
best_b, best_key = B_GRID[0], None
for b in B_GRID:
    model.bias_scale = b
    acc, macro, swf = score()
    print(f"{b:>11}{acc:>10.3f}{macro:>10.3f}{swf:>11.3f}")
    key = (round(macro, 4), round(swf, 4))
    if best_key is None or key > best_key:
        best_b, best_key = b, key
base_macro = best_key[0]

print(f"\nStage 2: smoothing (bias_scale = {best_b})")
print(f"{'switch_prior':>13}{'lexicon_conf':>14}{'accuracy':>10}{'macro-F1':>10}{'switch F1':>11}")
model.bias_scale = best_b
best_s, best_l, best_skey = None, 0.9, (-1, -1)
for s in S_GRID:
    for lam in L_GRID:
        model.switch_prior, model.lexicon_conf = s, lam
        acc, macro, swf = score()
        print(f"{s:>13}{lam:>14}{acc:>10.3f}{macro:>10.3f}{swf:>11.3f}")
        key = (round(macro, 4), round(swf, 4))
        if key > best_skey:
            best_s, best_l, best_skey = s, lam, key

if best_skey[0] - base_macro < MIN_GAIN:
    best_s, best_l = None, 0.9
    print(f"\nSmoothing gain {best_skey[0] - base_macro:+.3f} is below {MIN_GAIN}: left off.")

PARAMS_PATH.write_text(json.dumps(
    {"switch_prior": best_s, "lexicon_confidence": best_l, "bias_scale": best_b,
     "tuned_on": "data/eval/dev.txt"}, indent=2), encoding="utf-8")
print(f"\nSaved: switch_prior={best_s}, lexicon_confidence={best_l}, bias_scale={best_b}")