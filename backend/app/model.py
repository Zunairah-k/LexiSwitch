"""Token-level language identifier.

For each token:
  1. Unicode script gives the candidate languages (hard rule).
  2. If several candidates remain, look the word up in the dictionary (built from the
     training word lists, with hand-written function-word lists taking priority):
       listed under one language   -> that language              ("lexicon")
       listed under several        -> classifier chooses among
                                      those only                 ("lexicon+char-ngram-nb")
       not listed                  -> classifier chooses among
                                      all candidates             ("char-ngram-nb")
  3. The classifier is a character n-gram Naive Bayes. Its scores get a per-language
     offset (corrects the lean toward English), are divided by a temperature, and are
     renormalised over the candidate languages.
  4. Every token gets an emission distribution over the model's languages. An optional
     Viterbi pass picks the best language sequence, where changing language between
     neighbouring tokens costs `switch_prior` (None = every token decided independently).
"""
from dataclasses import dataclass

import joblib
import numpy as np

from .config import SCRIPT_LANGS, load_params, model_path
from .script_detect import detect_script
from .tokenizer import tokenize

OTHER = "other"
SCRIPT_CONFIDENCE = 0.999


@dataclass
class TokenPrediction:
    index: int
    text: str
    start: int
    end: int
    script: str
    language: str                     # final language code, or "other"
    method: str                       # script-rule | lexicon | lexicon+char-ngram-nb |
                                      # char-ngram-nb | no-letters | unsupported-script
    probability: float | None         # classifier probability (before context)
    runner_up: str | None
    runner_up_probability: float | None
    independent_language: str | None = None   # decision before context smoothing
    context_override: bool = False            # True if context changed the decision


class LanguageIdentifier:
    def __init__(self, vectorizer, classifier, temperature, lexicon,
                 use_lexicon=True, switch_prior=None, lexicon_conf=0.9, bias=None, bias_scale=1.0):
        self.vec = vectorizer
        self.clf = classifier
        self.T = temperature
        self.lexicon = lexicon
        self.use_lexicon = use_lexicon
        self.switch_prior = switch_prior
        self.lexicon_conf = lexicon_conf
        self.classes = list(classifier.classes_)
        self.index = {c: i for i, c in enumerate(self.classes)}
        self.bias = np.zeros(len(self.classes)) if bias is None else np.asarray(bias, dtype=float)
        self.bias_scale = bias_scale

    @classmethod
    def load(cls, langs=None, use_lexicon=True, use_context=True):
        b = joblib.load(model_path(langs))
        prm = load_params()
        return cls(b["vectorizer"], b["classifier"], b["temperature"], b["lexicon"],
                   use_lexicon=use_lexicon,
                   switch_prior=prm["switch_prior"] if use_context else None,
                   lexicon_conf=prm["lexicon_confidence"],
                   bias=b.get("bias"), bias_scale=prm["bias_scale"])

    def _plan(self, text: str):
        tokens = tokenize(text)
        plans = []
        for t in tokens:
            script = detect_script(t.text)
            if script == "NONE":
                plans.append((script, [], "no-letters"))
                continue
            cands = [l for l in SCRIPT_LANGS.get(script, []) if l in self.index]
            if not cands:
                plans.append((script, [], "unsupported-script"))
            elif len(cands) == 1:
                plans.append((script, cands, "script-rule"))
            else:
                hits = []
                if self.use_lexicon:
                    hits = [l for l in self.lexicon.get(t.text.lower(), []) if l in cands]
                if len(hits) == 1:
                    plans.append((script, hits, "lexicon"))
                elif len(hits) > 1:
                    plans.append((script, hits, "lexicon+char-ngram-nb"))
                else:
                    plans.append((script, cands, "char-ngram-nb"))
        return tokens, plans

    def _emission(self, support, probs, lam):
        """Distribution over all languages: `lam` of the mass goes to `support`
        (split by `probs`), the rest is shared by the other languages."""
        K = len(self.classes)
        idxs = [self.index[l] for l in support]
        e = np.empty(K)
        rest = [k for k in range(K) if k not in idxs]
        if rest:
            e[rest] = (1.0 - lam) / len(rest)
            e[idxs] = lam * np.asarray(probs)
        else:
            e[idxs] = probs
        return e

    def _decode(self, E):
        """Viterbi: best language sequence given emissions E (tokens x languages)."""
        if self.switch_prior is None or len(E) < 2:
            return E.argmax(axis=1)
        K, s = E.shape[1], self.switch_prior
        trans = np.full((K, K), np.log(s / (K - 1)))
        np.fill_diagonal(trans, np.log(1 - s))
        logE = np.log(np.maximum(E, 1e-12))
        delta, back = logE[0], []
        for t in range(1, len(E)):
            scores = delta[:, None] + trans
            back.append(scores.argmax(axis=0))
            delta = scores.max(axis=0) + logE[t]
        path = [int(delta.argmax())]
        for b in reversed(back):
            path.append(int(b[path[-1]]))
        path.reverse()
        return np.array(path)

    def predict(self, text: str) -> list[TokenPrediction]:
        tokens, plans = self._plan(text)

        need = [i for i, (_, _, m) in enumerate(plans) if "char-ngram-nb" in m]
        logp = {}
        if need:
            X = self.vec.transform([tokens[i].text for i in need])
            for i, row in zip(need, self.clf.predict_log_proba(X)):
                logp[i] = row + self.bias * self.bias_scale

        emis, nbp = {}, {}
        for i, (script, cands, method) in enumerate(plans):
            if method in ("no-letters", "unsupported-script"):
                continue
            if method == "script-rule":
                emis[i] = self._emission(cands, [1.0], SCRIPT_CONFIDENCE)
            elif method == "lexicon":
                emis[i] = self._emission(cands, [1.0], self.lexicon_conf)
            else:
                sub = logp[i][[self.index[l] for l in cands]] / self.T
                p = np.exp(sub - sub.max())
                p /= p.sum()
                nbp[i] = (cands, p)
                lam = self.lexicon_conf if method == "lexicon+char-ngram-nb" else SCRIPT_CONFIDENCE
                emis[i] = self._emission(cands, p, lam)

        order = sorted(emis)
        final = {}
        if order:
            path = self._decode(np.array([emis[i] for i in order]))
            final = dict(zip(order, path))

        results = []
        for i, t in enumerate(tokens):
            script, cands, method = plans[i]
            base = dict(index=t.index, text=t.text, start=t.start, end=t.end,
                        script=script, method=method)
            if i not in emis:
                results.append(TokenPrediction(**base, language=OTHER, probability=None,
                                               runner_up=None, runner_up_probability=None))
                continue
            lang = self.classes[int(final[i])]
            ind = self.classes[int(emis[i].argmax())]
            extra = dict(independent_language=ind, context_override=(lang != ind))
            if i in nbp:
                c, p = nbp[i]
                o = np.argsort(-p)
                results.append(TokenPrediction(
                    **base, language=lang, probability=float(p[o[0]]),
                    runner_up=c[o[1]], runner_up_probability=float(p[o[1]]), **extra))
            else:
                results.append(TokenPrediction(**base, language=lang, probability=None,
                                               runner_up=None, runner_up_probability=None,
                                               **extra))
        return results