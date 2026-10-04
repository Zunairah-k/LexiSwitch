"""Code-switch analysis and statistics computed from token predictions.

Definitions (also document these in your report):
  language-bearing token : a token whose language is not "other"
                           (numbers, symbols and unsupported scripts are neutral
                           and are skipped, never counted as a switch).
  n                      : number of language-bearing tokens.
  segment                : maximal run of consecutive language-bearing tokens
                           with the same language.
  language sequence      : the languages of the segments in order.
  switch (transition)    : a boundary between two consecutive segments.
                           switch count = number of segments - 1.
  switch position        : 1-based position of the first token after the boundary.
  distribution           : tokens per language / n.
  dominant language      : language(s) with the most tokens (several if tied).
  switch density         : switches / (n - 1), the fraction of adjacent token pairs
                           that are a language change (undefined if n < 2).
  mixing index (M)       : (1 - sum p_j^2) / ((k - 1) * sum p_j^2), where p_j is the
                           token share of language j and k the number of languages the
                           model can identify. 0 = one language, 1 = perfectly even mix.
"""
from collections import Counter
from dataclasses import asdict, dataclass

from .model import OTHER, TokenPrediction


@dataclass
class Segment:
    language: str
    token_indices: list[int]
    start_index: int
    end_index: int


@dataclass
class Switch:
    from_language: str
    to_language: str
    from_token_index: int
    to_token_index: int
    position: int


def analyze(preds: list[TokenPrediction], num_languages: int, top_uncertain: int = 5) -> dict:
    lang_toks = [p for p in preds if p.language != OTHER]
    n = len(lang_toks)

    segments: list[Segment] = []
    for p in lang_toks:
        if segments and segments[-1].language == p.language:
            segments[-1].token_indices.append(p.index)
            segments[-1].end_index = p.index
        else:
            segments.append(Segment(p.language, [p.index], p.index, p.index))

    switches = [
        Switch(a.language, b.language, a.token_indices[-1], b.token_indices[0],
               b.token_indices[0] + 1)
        for a, b in zip(segments, segments[1:])
    ]

    counts = Counter(p.language for p in lang_toks)
    order = list(dict.fromkeys(p.language for p in lang_toks))   # first appearance
    distribution = [
        {"language": l, "tokens": counts[l], "proportion": counts[l] / n}
        for l in sorted(order, key=lambda l: -counts[l])
    ]
    top = max(counts.values()) if counts else 0
    dominant = [l for l in order if counts[l] == top] if counts else []

    density = len(switches) / (n - 1) if n > 1 else None

    mixing = None
    if n > 0 and num_languages > 1:
        sum_sq = sum((c / n) ** 2 for c in counts.values())
        mixing = (1 - sum_sq) / ((num_languages - 1) * sum_sq)

    scored = [p for p in preds if p.probability is not None]
    scored.sort(key=lambda p: p.probability - p.runner_up_probability)
    uncertain = [{
        "index": p.index, "token": p.text,
        "language": p.independent_language or p.language, "probability": p.probability,
        "runner_up": p.runner_up, "runner_up_probability": p.runner_up_probability,
        "margin": p.probability - p.runner_up_probability,
    } for p in scored[:top_uncertain]]

    return {
        "tokens_total": len(preds),
        "tokens_analyzed": n,
        "tokens_neutral": len(preds) - n,
        "languages": order,
        "language_count": len(order),
        "distribution": distribution,
        "dominant_languages": dominant,
        "sequence": [s.language for s in segments],
        "segments": [asdict(s) for s in segments],
        "switches": [asdict(s) for s in switches],
        "switch_count": len(switches),
        "switch_density": density,
        "mixing_index": mixing,
        "context_overrides": sum(1 for p in preds if p.context_override),
        "scripts": list(dict.fromkeys(p.script.title() for p in preds if p.script != "NONE")),
        "uncertain_tokens": uncertain,
    }