"""Token-level language identifier.

For each token:
  1. Unicode script gives the candidate languages (hard rule).
  2. If several candidates remain, look the word up in the lexicon built from
     the training word lists.
       - listed under exactly one language  -> that language   ("lexicon")
       - listed under several languages     -> classifier chooses among
                                               those only      ("lexicon+char-ngram-nb")
       - not listed                         -> classifier chooses among all
                                               candidates      ("char-ngram-nb")
  3. The classifier is a character n-gram Naive Bayes; its probabilities are
     temperature-scaled, then renormalised over the candidate languages.
"""
from dataclasses import dataclass

import joblib
import numpy as np

from .config import SCRIPT_LANGS, model_path
from .script_detect import detect_script
from .tokenizer import tokenize

OTHER = "other"


@dataclass
class TokenPrediction:
    index: int
    text: str
    start: int
    end: int
    script: str
    language: str                     # language code, or "other"
    method: str                       # script-rule | lexicon | lexicon+char-ngram-nb |
                                      # char-ngram-nb | no-letters | unsupported-script
    probability: float | None         # only when the classifier made the decision
    runner_up: str | None
    runner_up_probability: float | None


class LanguageIdentifier:
    def __init__(self, vectorizer, classifier, temperature, lexicon, use_lexicon=True):
        self.vec = vectorizer
        self.clf = classifier
        self.T = temperature
        self.lexicon = lexicon
        self.use_lexicon = use_lexicon
        self.classes = list(classifier.classes_)
        self.index = {c: i for i, c in enumerate(self.classes)}

    @classmethod
    def load(cls, langs=None, use_lexicon=True):
        b = joblib.load(model_path(langs))
        return cls(b["vectorizer"], b["classifier"], b["temperature"],
                   b["lexicon"], use_lexicon)

    def _plan(self, text: str):
        """Decide script, candidate languages and method for every token."""
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

    def predict(self, text: str) -> list[TokenPrediction]:
        tokens, plans = self._plan(text)

        need = [i for i, (_, _, m) in enumerate(plans) if "char-ngram-nb" in m]
        logp = {}
        if need:
            X = self.vec.transform([tokens[i].text for i in need])
            for i, row in zip(need, self.clf.predict_log_proba(X)):
                logp[i] = row

        results = []
        for i, t in enumerate(tokens):
            script, cands, method = plans[i]
            base = dict(index=t.index, text=t.text, start=t.start, end=t.end,
                        script=script, method=method)
            if method in ("no-letters", "unsupported-script"):
                results.append(TokenPrediction(**base, language=OTHER, probability=None,
                                               runner_up=None, runner_up_probability=None))
            elif method in ("script-rule", "lexicon"):
                results.append(TokenPrediction(**base, language=cands[0], probability=None,
                                               runner_up=None, runner_up_probability=None))
            else:
                sub = logp[i][[self.index[l] for l in cands]] / self.T
                p = np.exp(sub - sub.max())
                p /= p.sum()                       # renormalise over candidates only
                order = np.argsort(-p)
                results.append(TokenPrediction(
                    **base, language=cands[order[0]], probability=float(p[order[0]]),
                    runner_up=cands[order[1]], runner_up_probability=float(p[order[1]])))
        return results