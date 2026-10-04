"""Trains the character n-gram Naive Bayes for a set of languages.

Usage (from backend/):
    python scripts\\train_model.py                 # active languages (en,hi,te)
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
from sklearn.feature_extraction.text import CountVectorizer  # noqa: E402
from sklearn.metrics import classification_report, confusion_matrix  # noqa: E402
from sklearn.model_selection import GroupShuffleSplit  # noqa: E402
from sklearn.naive_bayes import MultinomialNB  # noqa: E402

from app.config import (ACTIVE_LANGUAGES, ALPHA, DATA_PATH, LANGUAGES,  # noqa: E402
                        NGRAM_RANGE, model_path)
from app.script_detect import detect_script  # noqa: E402


def make_model():
    vec = CountVectorizer(analyzer="char_wb", ngram_range=NGRAM_RANGE, lowercase=True)
    clf = MultinomialNB(alpha=ALPHA, fit_prior=False)  # uniform class priors
    return vec, clf


def nll_and_conf(logp, y_idx, t):
    """Mean negative log-likelihood and mean top probability at temperature t."""
    z = logp / t
    z = z - logsumexp(z, axis=1, keepdims=True)
    nll = -z[np.arange(len(y_idx)), y_idx].mean()
    return float(nll), float(np.exp(z).max(axis=1).mean())


def fit_temperature(logp, y_idx):
    """Pick the temperature T >= 1 that minimises validation log-loss."""
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

    # Group split: all spellings of one word stay on the same side.
    tr, va = next(GroupShuffleSplit(n_splits=1, test_size=0.1, random_state=42)
                  .split(words, labels, groups))

    vec, clf = make_model()
    clf.fit(vec.fit_transform([words[i] for i in tr]), [labels[i] for i in tr])
    classes = list(clf.classes_)
    cidx = {c: i for i, c in enumerate(classes)}

    # Evaluate on Latin-script (romanized) held-out words: the hard case.
    latin = [i for i in va if detect_script(words[i]) == "LATIN"]
    X = vec.transform([words[i] for i in latin])
    logp = clf.predict_log_proba(X)
    y_idx = np.array([cidx[labels[i]] for i in latin])
    y_true = [labels[i] for i in latin]
    y_pred = [classes[j] for j in logp.argmax(axis=1)]

    print(f"\nHeld-out words (all scripts): {len(va)}")
    print(f"Held-out Latin-script words: {len(latin)}")
    print(f"Latin-script accuracy: {(logp.argmax(axis=1) == y_idx).mean():.4f}\n")
    print(classification_report(y_true, y_pred, labels=classes, zero_division=0, digits=3))
    cm = confusion_matrix(y_true, y_pred, labels=classes)
    print("Confusion matrix (rows = true, columns = predicted):")
    print("      " + "".join(f"{c:>7}" for c in classes))
    for c, row in zip(classes, cm):
        print(f"{c:>6}" + "".join(f"{v:>7}" for v in row))

    # Probability calibration (temperature scaling) on held-out words.
    t = fit_temperature(logp, y_idx)
    acc = float((logp.argmax(axis=1) == y_idx).mean())
    nll1, conf1 = nll_and_conf(logp, y_idx, 1.0)
    nllT, confT = nll_and_conf(logp, y_idx, t)
    print(f"\nCalibration (accuracy on these words = {acc:.3f}):")
    print(f"  T = 1.0 : log-loss {nll1:.3f}, mean top probability {conf1:.3f}")
    print(f"  T = {t:.1f} : log-loss {nllT:.3f}, mean top probability {confT:.3f}")

    # Final model: refit on ALL words, build the lexicon, save.
    vec, clf = make_model()
    clf.fit(vec.fit_transform(words), labels)
    lex: dict[str, set[str]] = {}
    for w, l in zip(words, labels):
        if w.isascii():
            lex.setdefault(w.lower(), set()).add(l)
    lexicon = {w: sorted(s) for w, s in lex.items()}
    ambiguous = sum(1 for s in lexicon.values() if len(s) > 1)
    print(f"\nLexicon: {len(lexicon)} Latin-script words, {ambiguous} listed under >1 language")

    out = model_path(langs)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"vectorizer": vec, "classifier": clf, "temperature": t,
                 "lexicon": lexicon, "languages": langs}, out)
    print(f"Saved model to {out}")


if __name__ == "__main__":
    main()