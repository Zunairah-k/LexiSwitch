import unittest

from app.analysis import analyze
from app.model import TokenPrediction


def mk(i, text, lang, p=None, runner=None, rp=None):
    other = lang == "other"
    return TokenPrediction(
        index=i, text=text, start=0, end=len(text),
        script="NONE" if other else "LATIN", language=lang,
        method="char-ngram-nb" if p is not None else "lexicon",
        probability=p, runner_up=runner, runner_up_probability=rp)


def build(words, langs):
    return [mk(i, w, l) for i, (w, l) in enumerate(zip(words, langs))]


class AnalysisTests(unittest.TestCase):
    def test_example_sentence(self):
        words = "Nenu assignment submit chesanu but mam asked for corrections".split()
        langs = ["te", "en", "en", "te", "en", "en", "en", "en", "en"]
        r = analyze(build(words, langs), num_languages=3)
        self.assertEqual(r["sequence"], ["te", "en", "te", "en"])
        self.assertEqual(r["switch_count"], 3)
        self.assertEqual(r["switches"][0], {
            "from_language": "te", "to_language": "en",
            "from_token_index": 0, "to_token_index": 1, "position": 2})
        self.assertEqual(r["dominant_languages"], ["en"])
        self.assertAlmostEqual(r["switch_density"], 3 / 8)
        self.assertAlmostEqual(r["mixing_index"], 28 / 106)   # 1-53/81 over 2*53/81

    def test_neutral_tokens_are_skipped(self):
        r = analyze(build(["kal", "123", "hai"], ["hi", "other", "hi"]), 3)
        self.assertEqual(r["tokens_total"], 3)
        self.assertEqual(r["tokens_analyzed"], 2)
        self.assertEqual(r["switch_count"], 0)
        self.assertEqual(r["segments"][0]["token_indices"], [0, 2])

    def test_empty_and_single(self):
        r = analyze([], 3)
        self.assertIsNone(r["switch_density"])
        self.assertIsNone(r["mixing_index"])
        self.assertEqual(r["dominant_languages"], [])
        r = analyze(build(["hello"], ["en"]), 3)
        self.assertIsNone(r["switch_density"])
        self.assertEqual(r["mixing_index"], 0.0)

    def test_tie_and_density(self):
        r = analyze(build(["hello", "namaste"], ["en", "hi"]), 3)
        self.assertEqual(r["dominant_languages"], ["en", "hi"])
        self.assertAlmostEqual(r["switch_density"], 1.0)
        self.assertAlmostEqual(r["mixing_index"], 0.5)

    def test_uncertain_sorted_by_margin(self):
        preds = [mk(0, "a", "en", 0.9, "hi", 0.1), mk(1, "b", "hi", 0.55, "en", 0.45)]
        r = analyze(preds, 3)
        self.assertEqual(r["uncertain_tokens"][0]["token"], "b")


if __name__ == "__main__":
    unittest.main()