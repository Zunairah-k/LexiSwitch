"""Evaluate token-level language ID and switch detection on hand-labeled sentences.

Gold format, one sentence per line, every word written as word/label:
    Nenu/te assignment/en submit/en chesanu/te but/en mam/en corrections/en
Labels: en, hi, te, other.  Blank lines and lines starting with # are ignored.
`other` tokens (names, numbers, emojis, other languages) are not scored.

Usage (from backend/):
    python scripts\\evaluate.py data\\eval\\dev.txt
    python scripts\\evaluate.py data\\eval\\test.txt
"""
import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, f1_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from app.analysis import analyze  # noqa: E402
from app.model import OTHER, LanguageIdentifier, TokenPrediction  # noqa: E402
from app.tokenizer import tokenize  # noqa: E402


def f(x):
    return "n/a" if x is None else f"{x:.3f}"


def load_gold(path: Path, valid: set[str]):
    sentences, problems = [], []
    for ln, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        words, labels, bad = [], [], False
        for chunk in line.split():
            word, sep, label = chunk.rpartition("/")
            if not sep or not word or label not in valid:
                problems.append(f"line {ln}: bad item '{chunk}' "
                                f"(expected word/label, label in {sorted(valid)})")
                bad = True
                continue
            words.append(word)
            labels.append(label)
        if bad:
            continue
        text = " ".join(words)
        toks = [t.text for t in tokenize(text)]
        if len(toks) != len(words):
            problems.append(f"line {ln}: {len(words)} labeled words but the tokenizer "
                            f"found {len(toks)} tokens: {toks}")
            continue
        sentences.append((text, labels))
    return sentences, problems


def evaluate(model, sentences):
    rows, per_sentence, pairs = [], [], []
    k = len(model.classes)
    for sid, (text, gold) in enumerate(sentences, 1):
        preds = model.predict(text)
        gold_preds = [
            TokenPrediction(index=p.index, text=p.text, start=p.start, end=p.end,
                            script=p.script, language=g, method="gold",
                            probability=None, runner_up=None, runner_up_probability=None)
            for p, g in zip(preds, gold)]
        pairs.append((analyze(gold_preds, k), analyze(preds, k)))
        correct = total = 0
        for p, g in zip(preds, gold):
            rows.append({"sid": sid, "pos": p.index + 1, "token": p.text, "gold": g,
                         "pred": p.language, "method": p.method,
                         "prob": p.probability, "runner_up": p.runner_up,
                         "sentence": text})
            if g != OTHER:
                total += 1
                correct += p.language == g
        per_sentence.append((correct, total))
    return {"rows": rows, "per_sentence": per_sentence, "pairs": pairs}


def token_metrics(rows, classes):
    scored = [r for r in rows if r["gold"] != OTHER]
    y_true = [r["gold"] for r in scored]
    y_pred = [r["pred"] for r in scored]
    acc = float(np.mean([a == b for a, b in zip(y_true, y_pred)]))
    present = [c for c in classes if c in set(y_true)]
    macro = f1_score(y_true, y_pred, labels=present, average="macro", zero_division=0)
    return scored, y_true, y_pred, acc, float(macro), present


def bootstrap_ci(per_sentence, n_boot=1000, seed=42):
    arr = np.array(per_sentence, dtype=float)
    rng = np.random.default_rng(seed)
    accs = []
    for _ in range(n_boot):
        s = arr[rng.integers(0, len(arr), len(arr))].sum(axis=0)
        if s[1] > 0:
            accs.append(s[0] / s[1])
    return np.percentile(accs, [2.5, 97.5])


def switch_summary(pairs):
    tp = pp = gp = exact_count = exact_seq = abs_err = 0
    for g, p in pairs:
        gb = {(s["to_token_index"], s["from_language"], s["to_language"]) for s in g["switches"]}
        pb = {(s["to_token_index"], s["from_language"], s["to_language"]) for s in p["switches"]}
        tp += len(gb & pb)
        pp += len(pb)
        gp += len(gb)
        exact_count += g["switch_count"] == p["switch_count"]
        exact_seq += g["sequence"] == p["sequence"]
        abs_err += abs(g["switch_count"] - p["switch_count"])
    n = len(pairs)
    prec = tp / pp if pp else None
    rec = tp / gp if gp else None
    f1 = None
    if prec is not None and rec is not None:
        f1 = 2 * prec * rec / (prec + rec) if prec + rec > 0 else 0.0
    return {"gold_switches": gp, "pred_switches": pp, "matched": tp,
            "precision": prec, "recall": rec, "f1": f1,
            "count_exact": exact_count / n, "sequence_exact": exact_seq / n,
            "count_mae": abs_err / n}


def describe(res, sentences):
    gold_counts = {}
    for r in res["rows"]:
        gold_counts[r["gold"]] = gold_counts.get(r["gold"], 0) + 1
    cs = sum(1 for g, _ in res["pairs"] if g["switch_count"] > 0)
    gs = sum(g["switch_count"] for g, _ in res["pairs"])
    print(f"Sentences: {len(sentences)}  (code-switched: {cs}, single-language: {len(sentences) - cs})")
    print(f"Tokens: {len(res['rows'])}  by gold label: {dict(sorted(gold_counts.items()))}")
    print(f"Gold switch points: {gs}")


def print_full(res, classes, out_dir, tag):
    scored, y_true, y_pred, acc, macro, present = token_metrics(res["rows"], classes)
    lo, hi = bootstrap_ci(res["per_sentence"])
    print(f"Scored tokens (gold label is not 'other'): {len(scored)}")
    print(f"Token accuracy: {acc:.4f}   (95% bootstrap interval over sentences: {lo:.3f} to {hi:.3f})")
    print(f"Macro-F1 over languages present: {macro:.4f}\n")
    print(classification_report(y_true, y_pred, labels=present, zero_division=0, digits=3))

    labels = list(classes) + [OTHER]
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    print("Confusion matrix (rows = gold, columns = predicted):")
    print("      " + "".join(f"{c:>7}" for c in labels))
    for c, row in zip(labels, cm):
        if c in present:
            print(f"{c:>6}" + "".join(f"{v:>7}" for v in row))

    neutral = [r for r in res["rows"] if r["gold"] == OTHER]
    if neutral:
        hit = sum(r["pred"] == OTHER for r in neutral)
        print(f"\nGold 'other' tokens (not scored): {len(neutral)}; model also said 'other' for {hit}")

    by_method = {}
    for r in scored:
        m = by_method.setdefault(r["method"], [0, 0])
        m[0] += 1
        m[1] += r["gold"] == r["pred"]
    print("\nAccuracy by decision method:")
    for m, (n, c) in sorted(by_method.items()):
        print(f"  {m:<24}{n:>6} tokens   accuracy {c / n:.3f}")

    sw = switch_summary(res["pairs"])
    print("\nSwitch detection (a switch counts as found only if position AND language pair match):")
    print(f"  gold switches {sw['gold_switches']}, predicted {sw['pred_switches']}, matched {sw['matched']}")
    print(f"  precision {f(sw['precision'])}  recall {f(sw['recall'])}  F1 {f(sw['f1'])}")
    print(f"  sentences with exactly the right switch count: {sw['count_exact']:.3f}")
    print(f"  sentences with exactly the right language sequence: {sw['sequence_exact']:.3f}")
    print(f"  mean absolute error in switch count per sentence: {sw['count_mae']:.3f}")

    errors = [r for r in scored if r["gold"] != r["pred"]]
    print(f"\nErrors: {len(errors)} of {len(scored)} scored tokens")
    for r in errors[:40]:
        p = "-" if r["prob"] is None else f"{r['prob']:.2f}"
        print(f"  s{r['sid']:>3} pos {r['pos']:>2}  {r['token']:<16} gold {r['gold']} -> {r['pred']}  ({r['method']}, {p})")
    if len(errors) > 40:
        print(f"  ... {len(errors) - 40} more in the CSV")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"errors_{tag}.csv"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["sentence_id", "position", "token", "gold", "predicted", "method",
                    "probability", "runner_up", "sentence"])
        for r in errors:
            w.writerow([r["sid"], r["pos"], r["token"], r["gold"], r["pred"], r["method"],
                        "" if r["prob"] is None else f"{r['prob']:.4f}",
                        r["runner_up"] or "", r["sentence"]])
    print(f"Error list written to {path}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--langs", default=None)
    ap.add_argument("--out", default=str(ROOT.parent / "docs"))
    args = ap.parse_args()
    langs = args.langs.split(",") if args.langs else None

    full = LanguageIdentifier.load(langs)
    nb_only = LanguageIdentifier.load(langs, use_lexicon=False)
    sentences, problems = load_gold(Path(args.file), set(full.classes) | {OTHER})
    if problems:
        print("Fix these lines first:")
        for p in problems:
            print("  ", p)
        sys.exit(1)
    if not sentences:
        sys.exit("No sentences found.")

    print(f"=== {args.file} ===")
    res_full = evaluate(full, sentences)
    describe(res_full, sentences)
    print("\n--- Full pipeline (script rules + lexicon + character n-gram NB) ---")
    print_full(res_full, full.classes, Path(args.out), Path(args.file).stem)

    res_nb = evaluate(nb_only, sentences)
    print("\n--- Ablation ---")
    print(f"{'configuration':<28}{'accuracy':>10}{'macro-F1':>10}{'switch P':>10}{'switch R':>10}{'switch F1':>11}")
    for name, res in [("lexicon + n-gram NB", res_full), ("n-gram NB only", res_nb)]:
        _, _, _, acc, macro, _ = token_metrics(res["rows"], full.classes)
        sw = switch_summary(res["pairs"])
        print(f"{name:<28}{acc:>10.3f}{macro:>10.3f}{f(sw['precision']):>10}"
              f"{f(sw['recall']):>10}{f(sw['f1']):>11}")


if __name__ == "__main__":
    main()