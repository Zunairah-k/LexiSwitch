"""Trains the character n-gram Naive Bayes for a set of languages.

Usage (from backend/):
    python scripts\\train_model.py                          # active languages (en,hi,te)
    python scripts\\train_model.py --langs en,hi,te,mr,ur   # experiment
"""
import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import joblib  # noqa: E402
import numpy as np  # noqa: E402
from scipy.special import logsumexp  # noqa: E402
from wordfreq import top_n_list  # noqa: E402
from sklearn.feature_extraction.text import CountVectorizer  # noqa: E402
from sklearn.metrics import classification_report, confusion_matrix  # noqa: E402
from sklearn.model_selection import GroupShuffleSplit  # noqa: E402
from sklearn.naive_bayes import MultinomialNB  # noqa: E402

from app.config import (ACTIVE_LANGUAGES, ALPHA, DATA_PATH, LANGUAGES,  # noqa: E402
                        NGRAM_RANGE, model_path)
from app.function_words import FUNCTION_WORDS  # noqa: E402
from app.script_detect import detect_script  # noqa: E402


def make_model():
    vec = CountVectorizer(analyzer="char_wb", ngram_range=NGRAM_RANGE, lowercase=True)
    clf = MultinomialNB(alpha=ALPHA, fit_prior=False)  # uniform class priors
    return vec, clf


def macro_f1(y, pred, k_classes):
    scores = []
    for k in range(k_classes):
        tp = int(np.sum((pred == k) & (y == k)))
        fp = int(np.sum((pred == k) & (y != k)))
        fn = int(np.sum((pred != k) & (y == k)))
        scores.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    return float(np.mean(scores))


def fit_bias(logp, y_idx):
    """Per-language score offsets that maximise macro-F1 on held-out words.
    Corrects the model's systematic lean toward one class (English)."""
    k_classes = logp.shape[1]
    bias = np.zeros(k_classes)
    best = macro_f1(y_idx, (logp + bias).argmax(axis=1), k_classes)
    for _ in range(3):
        for k in range(k_classes):
            for v in np.arange(-20.0, 20.5, 0.5):
                trial = bias.copy()
                trial[k] = v
                s = macro_f1(y_idx, (logp + trial).argmax(axis=1), k_classes)
                if s > best + 1e-9:
                    best, bias = s, trial
    return bias


def nll_and_conf(logp, y_idx, t):
    z = logp / t
    z = z - logsumexp(z, axis=1, keepdims=True)
    nll = -z[np.arange(len(y_idx)), y_idx].mean()
    return float(nll), float(np.exp(z).max(axis=1).mean())


def fit_temperature(logp, y_idx):
    best_t, best_nll = 1.0, np.inf
    for t in np.arange(1.0, 40.5, 0.5):
        nll, _ = nll_and_conf(logp, y_idx, t)
        if nll < best_nll:
            best_t, best_nll = float(t), nll
    return best_t


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default=",".join(ACTIVE_LANGUAGES))
    langs = sorted(ap.parse_args().langs.split(","))
    for l in langs:
        if l not in LANGUAGES:
            sys.exit(f"Unknown language code: {l}")

    with open(DATA_PATH, encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r["label"] in langs]
    words = [r["word"] for r in rows]
    labels = [r["label"] for r in rows]
    groups = [r["group"] for r in rows]
    print(f"Languages: {langs}   training rows: {len(rows)}")

    tr, va = next(GroupShuffleSplit(n_splits=1, test_size=0.1, random_state=42)
                  .split(words, labels, groups))

    vec, clf = make_model()
    clf.fit(vec.fit_transform([words[i] for i in tr]), [labels[i] for i in tr])
    classes = list(clf.classes_)
    cidx = {c: i for i, c in enumerate(classes)}

    latin = [i for i in va if detect_script(words[i]) == "LATIN"]
    logp = clf.predict_log_proba(vec.transform([words[i] for i in latin]))
    y_idx = np.array([cidx[labels[i]] for i in latin])
    k_classes = len(classes)

    acc0 = float((logp.argmax(axis=1) == y_idx).mean())
    f10 = macro_f1(y_idx, logp.argmax(axis=1), k_classes)

    # English-bias correction (fitted on these held-out words).
    bias = fit_bias(logp, y_idx)
    logp_b = logp + bias
    pred_b = logp_b.argmax(axis=1)
    acc1 = float((pred_b == y_idx).mean())
    f11 = macro_f1(y_idx, pred_b, k_classes)

    print(f"\nHeld-out words (all scripts): {len(va)}; Latin-script: {len(latin)}")
    print(f"Before bias correction: accuracy {acc0:.4f}, macro-F1 {f10:.4f}")
    print(f"After  bias correction: accuracy {acc1:.4f}, macro-F1 {f11:.4f}")
    print("Offsets:", {c: round(float(v), 1) for c, v in zip(classes, bias)})
    print("(Offsets and temperature are fitted on these same words, so these numbers are\n"
          " not an independent test; the sentence sets are.)\n")

    y_true = [classes[j] for j in y_idx]
    y_pred = [classes[j] for j in pred_b]
    print(classification_report(y_true, y_pred, labels=classes, zero_division=0, digits=3))
    cm = confusion_matrix(y_true, y_pred, labels=classes)
    print("Confusion matrix (rows = true, columns = predicted):")
    print("      " + "".join(f"{c:>7}" for c in classes))
    for c, row in zip(classes, cm):
        print(f"{c:>6}" + "".join(f"{v:>7}" for v in row))

    t = fit_temperature(logp_b, y_idx)
    nll1, conf1 = nll_and_conf(logp_b, y_idx, 1.0)
    nllT, confT = nll_and_conf(logp_b, y_idx, t)
    print(f"\nCalibration (accuracy on these words = {acc1:.3f}):")
    print(f"  T = 1.0 : log-loss {nll1:.3f}, mean top probability {conf1:.3f}")
    print(f"  T = {t:.1f} : log-loss {nllT:.3f}, mean top probability {confT:.3f}")

    # Final model: refit on ALL words, build the dictionary, apply function words.
    vec, clf = make_model()
    clf.fit(vec.fit_transform(words), labels)
    lex: dict[str, set[str]] = {}
    for w, l in zip(words, labels):
        if w.isascii():
            lex.setdefault(w.lower(), set()).add(l)

        # Very frequent English words stay English unless a function-word list says otherwise.
    if "en" in langs:
        for w in top_n_list("en", 300):
            if w.isascii() and w.replace("'", "").isalpha():
                lex[w.lower()] = {"en"}

    override: dict[str, set[str]] = {}
    for lang, ws in FUNCTION_WORDS.items():
        if lang in langs:
            for w in ws:
                override.setdefault(w, set()).add(lang)
    for w, s in override.items():
        lex[w] = s
    lexicon = {w: sorted(s) for w, s in lex.items()}
    ambiguous = sum(1 for s in lexicon.values() if len(s) > 1)
    print(f"\nDictionary: {len(lexicon)} Latin-script words, {ambiguous} listed under >1 language; "
          f"{len(override)} words set by the function-word lists")

    out = model_path(langs)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"vectorizer": vec, "classifier": clf, "temperature": t,
                 "lexicon": lexicon, "languages": langs,
                 "bias": [float(v) for v in bias]}, out)
    print(f"Saved model to {out}")


if __name__ == "__main__":
    main()