"""Builds the word-level training file (word,label,group) for all languages.

Indian languages: romanized AND native-script words from the Dakshina lexicons.
English: most frequent words from the `wordfreq` package.
`group` ties together every spelling of the same underlying word, so that the
train/validation split never puts one word's spellings on both sides.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wordfreq import top_n_list  # noqa: E402
from app.config import DATA_PATH, INDIC_CODES, MAX_WORDS_PER_LANG  # noqa: E402

RAW = ROOT / "data" / "raw" / "dakshina_dataset_v1.0"


def load_lexicon(code: str):
    """Return (roman_counts, native_counts, roman_to_native) or None."""
    files = sorted((RAW / code / "lexicons").glob("*.tsv"))
    if not files:
        return None
    roman: dict[str, int] = {}
    native: dict[str, int] = {}
    group: dict[str, str] = {}
    for f in files:
        with open(f, encoding="utf-8", newline="") as fh:
            for row in csv.reader(fh, delimiter="\t", quoting=csv.QUOTE_NONE):
                if len(row) < 2:
                    continue
                nat, rom = row[0].strip(), row[1].strip().lower()
                n = int(row[2]) if len(row) > 2 and row[2].strip().isdigit() else 1
                if rom.isascii() and rom.isalpha():
                    roman[rom] = roman.get(rom, 0) + n
                    group.setdefault(rom, nat)
                if nat and not nat.isascii() and " " not in nat:
                    native[nat] = native.get(nat, 0) + n
    return roman, native, group


def top(counts: dict[str, int]) -> list[str]:
    return sorted(counts, key=counts.get, reverse=True)[:MAX_WORDS_PER_LANG]


def english_words() -> list[str]:
    words = [w for w in top_n_list("en", MAX_WORDS_PER_LANG * 2)
             if w.isascii() and w.replace("'", "").isalpha()]
    return words[:MAX_WORDS_PER_LANG]


def main() -> None:
    entries: dict[str, dict[str, str]] = {}   # label -> {word: group}
    entries["en"] = {w: f"en:{w}" for w in english_words()}
    print(f"{'lang':<6}{'romanized':>10}{'native':>10}")
    print(f"{'en':<6}{len(entries['en']):>10}{'-':>10}")

    for code in INDIC_CODES:
        loaded = load_lexicon(code)
        if loaded is None:
            print(f"{code:<6} WARNING: no lexicon .tsv files found, skipped")
            continue
        roman_counts, native_counts, roman_group = loaded
        roman_top, native_top = top(roman_counts), top(native_counts)
        d: dict[str, str] = {}
        for w in roman_top:
            d[w] = f"{code}:{roman_group[w]}"
        for w in native_top:
            d.setdefault(w, f"{code}:{w}")
        entries[code] = d
        print(f"{code:<6}{len(roman_top):>10}{len(native_top):>10}")

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["word", "label", "group"])
        for label, d in entries.items():
            for w, g in d.items():
                writer.writerow([w, label, g])

    labels_of: dict[str, set[str]] = defaultdict(set)
    for label, d in entries.items():
        for w in d:
            labels_of[w].add(label)
    shared = {w for w, s in labels_of.items() if len(s) > 1}
    print(f"\nDistinct words: {len(labels_of)}; "
          f"appearing under more than one language: {len(shared)}")
    for label, d in entries.items():
        n = sum(1 for w in d if w in shared)
        print(f"  {label}: {n} of {len(d)} words also appear under another language")


if __name__ == "__main__":
    main()