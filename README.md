# LexiSwitch — Multilingual Token Analysis

Token-level language identification and code-switch detection for **English, Hindi and Telugu**.
Built for JNTUH R23 Natural Language Processing, **Unit III — Multilingual Issues**.

Given text that mixes languages, LexiSwitch labels every word with its language, builds the
language sequence, finds the points where the language changes, computes mixing statistics, and
shows the result in an interactive web interface.

```
Nenu assignment submit chesanu but mam asked for corrections
 te      en        en       te     en   te    en    en       en
```

It is not a translator, a chatbot or a sentence-level language detector. No large language model is
used for identification: every decision comes from a rule, a dictionary, or a probability model
whose arithmetic can be shown by hand.

---

## How it works

```
text → tokenizer → script detection → dictionary lookup → character n-gram Naive Bayes
     → language sequence → switch points → statistics → web interface
```

| Stage | What it does |
|---|---|
| Tokenizer | Splits on whitespace and punctuation, strips punctuation at word edges, keeps character offsets. |
| Script detection | Reads the Unicode script of each word. A Telugu-script word can only be Telugu, so it is decided by a rule. |
| Dictionary lookup | A romanized word listed under exactly one language takes that language. Words listed under several languages (or none) go to the classifier. |
| Classifier | Multinomial Naive Bayes on character 1–4-grams (`char_wb`), uniform priors, add-0.1 smoothing. |
| Calibration | Temperature scaling (T fitted on held-out words) so probabilities are not overconfident. Scores are renormalised over the candidate languages. |
| Analysis | Segments, switches, distribution, dominant language, switch density, mixing index, least-certain tokens. Definitions are documented in `backend/app/analysis.py`. |

Every value shown in the interface comes from this pipeline. Probabilities appear only for words the
classifier actually decided; words decided by a script rule or dictionary match show "model output".

## Interface

- **Analyze:** animated language canvas, token inspector, language-flow timeline with numbered
  code-switch markers, language fingerprint, analysis summary with formulas, model-uncertainty list.
- **Compare text:** two texts side by side with the same measures and shared highlighting of words
  in the same language.

## Results

Evaluation uses hand-labeled sentences. The development set guided decisions; the test set was run
**once** after the model was frozen.

| Test set (70 sentences, 316 scored tokens) | Value |
|---|---|
| Token accuracy | 0.877 (95% bootstrap interval 0.840–0.911) |
| Macro-F1 | 0.875 |
| English precision / recall | 0.816 / 0.991 |
| Hindi precision / recall | 0.899 / 0.832 |
| Telugu precision / recall | 0.951 / 0.794 |
| Switch precision / recall / F1 | 0.782 / 0.755 / 0.768 |
| Same model without the dictionary | accuracy 0.839, switch F1 0.726 |

Other measured results:

- Development set (33 sentences, 169 tokens): accuracy 0.858.
- Held-out romanized dictionary words: 0.751 accuracy with three languages, 0.502 with thirteen.
- Calibration: log-loss 4.561 → 0.648 after temperature scaling (T = 15.5).
- Context smoothing (Viterbi) was tested on the development set and gave no meaningful gain, so it
  is disabled (`backend/app/tuned_params.json`).

Raw outputs are saved in `docs/`. The full write-up is in `docs/REPORT.md`.

## Setup (Windows PowerShell)

Requirements: Python 3.10+, Node 20.19+.

**Backend** (from `backend/`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Download the Dakshina dataset (see its GitHub page: `google-research-datasets/dakshina`) and extract
it so that `backend/data/raw/dakshina_dataset_v1.0/` exists, then:

```powershell
python scripts\prepare_data.py      # builds data\processed\train_words.csv
python scripts\train_model.py       # trains and saves models\langid_en-hi-te.joblib
uvicorn app.main:app --reload --port 8000
```

Interactive API docs: http://127.0.0.1:8000/docs

**Frontend** (from `frontend/`, in a second terminal):

```powershell
npm install
npm run dev
```

Open http://localhost:5173. The dev server proxies `/api` to the backend.

## API

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/api/health` | – | status and active languages |
| POST | `/api/analyze` | `{"text": "..."}` | tokens (language, method, probability) and the full analysis |
| POST | `/api/compare` | `{"text_a": "...", "text_b": "..."}` | `a` and `b`, each like `/api/analyze` |

## Testing and evaluation

```powershell
python -m unittest tests.test_analysis                 # hand-verified formula tests
python scripts\evaluate.py data\eval\dev.txt           # development set
python scripts\evaluate.py data\eval\test.txt          # test set (report this once)
python scripts\train_model.py --langs en,bn,gu,hi,kn,ml,mr,pa,sd,si,ta,te,ur   # 13-language experiment
```

Gold files hold one sentence per line, each word written as `word/label` with labels `en`, `hi`,
`te` or `other` (names, numbers and other languages; not scored).

## Project structure

```
lexiswitch/
├── README.md
├── backend/
│   ├── app/            config, tokenizer, script_detect, model, analysis, pipeline, main
│   ├── scripts/        prepare_data, train_model, evaluate, tune, try_model, try_analysis
│   ├── tests/          test_analysis.py
│   ├── data/eval/      dev.txt, test.txt (hand-labeled)
│   └── requirements.txt
├── frontend/           Vite + React + Tailwind + Framer Motion (src/components, src/lib)
└── docs/               REPORT.md, VIVA_PREP.md, saved results and error lists
```

Training data (`data/raw`, `data/processed`) and trained models (`models/`) are not committed; the
two scripts above regenerate them.

## Adding a language

1. Make sure it has training words (the Dakshina data already covers Tamil, Kannada, Malayalam,
   Bengali and others).
2. Add its code to `ACTIVE_LANGUAGES` in `backend/app/config.py` and retrain.
3. Add its color in `frontend/src/lib/languages.js`.
4. Add labeled test sentences **before** claiming it works.

## Limitations

- Each word is classified without context, so words shared between languages (for example `ki`,
  `lo`, `ho`) are often wrong.
- Romanized Indian languages are hard to tell apart; the thirteen-language experiment shows how
  much accuracy drops.
- The evaluation set is small, hand-made and labeled by a single annotator, so results do not
  automatically transfer to natural social-media text.
- Names and numbers are treated as neutral tokens and are not scored.

## Data and references

- Dakshina dataset (Roark et al., LREC 2020) for Hindi and Telugu romanized and native-script words.
  Check its license and citation on the official page.
- `wordfreq` package for English word frequencies.
- Bikel and Zitouni, *Multilingual Natural Language Processing Applications: From Theory to Practice*.
- Siddiqui and Tiwary, *Natural Language Processing and Information Retrieval*.
- Jurafsky and Martin, *Speech and Language Processing*.