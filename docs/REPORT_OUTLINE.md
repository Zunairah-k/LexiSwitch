# LexiSwitch: Token-Level Language Identification and Code-Switch Detection for English, Hindi and Telugu

**Course:** Natural Language Processing (JNTUH R23), Unit III — Multilingual Issues
**Student:** Zunairah Maasfa Khan  
---

## Abstract

People who speak several languages routinely mix them inside a single sentence, for example "Nenu
assignment submit chesanu but mam asked for corrections". Standard NLP tools that assume one
language per text handle such input poorly, and a single sentence-level language label hides where
the language changes. This project builds LexiSwitch, a system that identifies the language of every
word (token) in mixed English, Hindi and Telugu text, extracts the sequence of languages, locates
the code-switch points, and computes mixing statistics, with an interactive web interface for
inspecting the results. The identifier combines Unicode script rules, a dictionary lookup and a
character n-gram Naive Bayes classifier whose probabilities are calibrated by temperature scaling.
On a hand-labeled test set of 70 sentences (316 scored tokens), run once after the model was frozen,
the system reaches a token accuracy of 0.877 (95% bootstrap interval 0.840–0.911) and a switch-point
F1 of 0.768. Most remaining errors come from short words that exist in more than one language, which
cannot be resolved without context.

---

## 1. Introduction

### 1.1 Problem

Given multilingual or code-switched text, identify the language of each token and detect where the
text switches from one language to another. For the example sentence, the expected analysis is:

| Nenu | assignment | submit | chesanu | but | mam | asked | for | corrections |
|---|---|---|---|---|---|---|---|---|
| Telugu | English | English | Telugu | English | English | English | English | English |

The language sequence is Telugu → English → Telugu → English, with three switch points.

### 1.2 Motivation

Code-switching is common in everyday writing by multilingual speakers, including Telugu–English and
Hindi–English chat messages. Many such texts are also written in Latin script rather than the native
script, so script alone does not reveal the language. Token-level identification is the first step
for any later processing of such text.

### 1.3 Objectives

1. Identify the language of each token in text containing English, Hindi and Telugu, in Latin or
   native script.
2. Derive the language sequence and the switch points from the token labels.
3. Compute documented statistics: language distribution, dominant language, switch density and a
   mixing index.
4. Evaluate the system honestly with a development set and a separate test set, using accuracy,
   precision, recall, F1, a confusion matrix, per-language results and error analysis.
5. Present the results in an interactive interface in which every displayed value comes from the
   implemented pipeline.

### 1.4 Scope and non-goals

The system is not a translator, a chatbot, a sentiment analyzer or a sentence-level language
detector, and it does not use a large language model for identification. It is trained on word lists
for thirteen languages but **supports and evaluates only English, Hindi and Telugu**, because those
are the languages for which a labeled test set could be built. The design allows more languages to
be added.

---

## 2. Background and syllabus connection

### 2.1 Unit III: Multilingual Issues

This project addresses the unit's theme of processing text that involves several languages and
scripts. [Add the exact Unit III topics from your syllabus copy that this work covers, and the
chapter or section numbers of Bikel and Zitouni, Siddiqui and Tiwary, and Jurafsky and Martin that
you cite.]

### 2.2 Language identification

Language identification assigns a language label to a piece of text. For long texts, character
n-gram statistics work well. For single words the problem is harder because a word carries little
evidence, and because words are often shared between languages (homographs across languages).

### 2.3 Code-switching

Code-switching is the alternation between languages within a text or sentence. Analysing it requires
labels below the sentence level. Related measures from the code-switching literature include the
share of language changes between neighbouring words and an index of how evenly languages are
mixed. This project defines both explicitly (Section 4.6).

### 2.4 Naive Bayes with character n-grams

A Naive Bayes classifier picks the class that maximises the prior times the product of the feature
likelihoods, assuming features are independent given the class. Using character n-grams as features
captures prefixes, suffixes and spelling patterns, which differ between languages and also help for
words never seen in training.

### 2.5 Probability calibration

Naive Bayes multiplies many dependent features as if they were independent, so its probabilities
are typically too close to 0 or 1. Temperature scaling divides the log-scores by a single number T,
fitted on held-out data, which makes the probabilities more honest without changing which class
wins.

---

## 3. System design

### 3.1 Architecture

```
Frontend (React)  →  Backend API (FastAPI)  →  NLP pipeline  →  Analysis  →  JSON  →  Visualizations
```

### 3.2 Pipeline

```
text
 → tokenizer
 → Unicode script detection
 → dictionary lookup (romanized words)
 → character n-gram Naive Bayes (for ambiguous or unknown words)
 → language sequence and switch points
 → statistics
```

### 3.3 Design decisions

- **Reproducible and explainable:** every decision is a rule, a dictionary match or a computed
  probability. No text is sent to an LLM.
- **Three active languages:** the classifier chooses only among English, Hindi and Telugu
  (Section 6.2 shows why adding similar languages hurts).
- **Extensible:** the language list, the script-to-language table and the interface colors are
  configuration, not hard-coded logic.

---

## 4. Methodology

### 4.1 Tokenization

Text is split on whitespace and common punctuation. Punctuation and symbol characters at the edges of
a token are removed, while apostrophes inside words are kept (for example "I'm"). The tokenizer
records character offsets so the interface can map tokens back to the input. It does not use the
regular-expression word class `\w`, which would split Indic words at vowel signs.

### 4.2 Script detection

Each Unicode character has a name beginning with its script (for example LATIN or TELUGU). The
dominant script among a token's letters and combining marks is its script; tokens with no letters
(numbers, symbols) are marked neutral. A table maps scripts to possible languages: Telugu script →
Telugu only; Devanagari → Hindi (and Marathi, when active); Latin → every active language. When
only one language is possible, the label is assigned by rule.

### 4.3 Dictionary lookup

For Latin-script tokens, the lowercased word is looked up in a dictionary built from the training
word lists, mapping each word to the languages it appears under.

- Listed under one language: that language is chosen ("lexicon").
- Listed under several: the classifier chooses among those languages only ("lexicon + n-gram").
- Not listed: the classifier chooses among all active languages ("n-gram").

### 4.4 Character n-gram Naive Bayes

Features are character n-grams of length 1 to 4, computed on the word padded with spaces at both
ends. For a word w with n-gram counts c(g), the classifier scores each language L:

log P(L | w) ∝ log P(L) + Σ_g c(g) · log P(g | L),   with   P(g | L) = (count(g, L) + α) / (Σ_g′ count(g′, L) + α · |V|)

where α = 0.1 is the smoothing constant and |V| is the n-gram vocabulary size. Class priors are
uniform, because the language mix of real text is unknown. The n-gram range and α are standard
choices and were not tuned.

### 4.5 Calibration

The log-scores are divided by a temperature T, passed through a softmax, and renormalised over the
candidate languages for that token:

p(L | w) = softmax( log P(L | w) / T ), restricted to the candidate languages.

T was chosen from 1.0 to 40.0 in steps of 0.5 to minimise log-loss on held-out romanized words
(the fitted value for the three-language model is T = 15.5). Probabilities are shown in the
interface only for tokens the classifier decided.

### 4.6 Code-switch analysis

Definitions used throughout the project:

- **Language token:** a token whose language is not "other". Numbers, symbols and unsupported
  scripts are neutral; they are skipped and never create a switch. Let n be the number of language
  tokens.
- **Segment:** a maximal run of consecutive language tokens with the same language.
- **Language sequence:** the languages of the segments, in order.
- **Switch:** a boundary between two consecutive segments. Switch count = number of segments − 1.
- **Switch position:** the 1-based position of the first token after the boundary.
- **Distribution:** tokens per language divided by n. **Dominant language:** the language with the
  most tokens (several if tied).
- **Switch density:** switches ÷ (n − 1), the share of neighbouring word pairs where the language
  changes (undefined when n < 2).
- **Mixing index:** M = (1 − Σ pⱼ²) ÷ ((k − 1) · Σ pⱼ²), where pⱼ is language j's share of tokens
  and k is the number of languages the model can identify (here 3). M = 0 for one language and
  M = 1 for a perfectly even mix of all k languages.

**Worked example.** With the correct labels for the example sentence (te, en, en, te, en, en, en,
en, en): 4 segments, 3 switches, switch density 3/8 = 0.375, and shares p(en) = 7/9, p(te) = 2/9, so
Σp² = 53/81 and M = (28/81) ÷ (2 · 53/81) = 28/106 ≈ 0.264. The system actually labels "mam" as
Telugu, which produces 5 switches, density 0.625 and M = 0.40 for the same sentence. One wrong token
changes the switch statistics a great deal, which is why switch detection is evaluated separately
from token accuracy.

---

## 5. Data

### 5.1 Training data

- **Hindi and Telugu:** romanized and native-script words from the Dakshina lexicons, which pair
  native words with several attested Latin-script spellings and counts. For each language, up to
  20,000 romanized words and up to 20,000 native-script words are kept, ranked by attestation count.
- **English:** the 20,000 most frequent English words from the `wordfreq` package, including
  words with apostrophes.
- The three-language model trains on 100,000 words (English 20,000; Hindi 40,000; Telugu 40,000).
  The dictionary holds 53,440 Latin-script words, of which 5,463 are listed under more than one
  language.
- Dictionary words were also extracted for ten other languages from the same dataset, used only in
  the thirteen-language experiment.

The cap of 20,000 words per language and form is a design choice to keep the classes balanced.

### 5.2 Held-out dictionary words

For model training diagnostics, 10% of words are held out with a **group split**: the Dakshina data
contains several romanizations of the same native word, so all spellings of one word are kept on the
same side of the split. This prevents a spelling in training from leaking its sibling spelling into
the held-out set.

### 5.3 Evaluation sentences

Two sets of hand-labeled sentences, written to resemble casual mixed-language messages:

| Set | Sentences | Code-switched | Single-language | Tokens (en / hi / te) | Gold switch points |
|---|---|---|---|---|---|
| Development | 33 | 29 | 4 | 169 (67 / 50 / 52) | 77 |
| Test | 70 | 62 | 8 | 316 (112 / 107 / 97) | 147 |

Each sentence has one label per word: `en`, `hi`, `te`, or `other` (names, numbers and words from other
languages; not scored).

**Labeling rules.** A word is labeled by the language it belongs to in the sentence. English loanwords
inside Telugu or Hindi sentences ("assignment", "college", "mam") are English. Words valid in two
languages are labeled by meaning. Both languages are labeled whether typed in Latin or native
script.

### 5.4 Provenance and protocol

[State accurately how the evaluation sentences were produced. Suggested wording, edit to match what
actually happened: "The sentences were drafted with the help of an AI assistant and labeled word by
word. All labels were then reviewed by the author, and the Telugu labels were checked by ____."]

The development set was used for all decisions, including testing a context-smoothing step
(Section 6.5). The model and its parameters were then frozen and committed to version control, and
the test set was evaluated **once**. The test numbers below are those of that single run. All
evaluation data has a single annotator, which is a limitation (Section 9).

---

## 6. Experiments and results

### 6.1 Held-out dictionary words (three languages)

On 6,021 held-out Latin-script words, the n-gram classifier alone reaches accuracy 0.751.

| Language | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| English | 0.642 | 0.966 | 0.771 | 1,984 |
| Hindi | 0.858 | 0.507 | 0.638 | 2,066 |
| Telugu | 0.857 | 0.789 | 0.822 | 1,971 |

Confusion matrix (rows = true, columns = predicted):

| | en | hi | te |
|---|---|---|---|
| en | 1,917 | 51 | 16 |
| hi | 775 | 1,048 | 243 |
| te | 294 | 122 | 1,555 |

Many romanized Hindi words are labeled English: single words carry little evidence, and short
romanized Hindi spellings resemble English letter patterns.

### 6.2 Three languages versus thirteen

The same method trained on all thirteen languages gives accuracy 0.502 on 25,866 held-out Latin-script
words (an earlier run with a random instead of group split gave 0.504, so the leak was small).

| Setting | Latin-script accuracy | Hindi recall | English precision |
|---|---|---|---|
| 3 languages | 0.751 | 0.507 | 0.642 |
| 13 languages | 0.502 | 0.154 | 0.336 |

Adding closely related languages written in Latin script (Hindi, Urdu, Punjabi, Sindhi, Marathi,
Gujarati and others share a lot of vocabulary and spelling patterns) sharply reduces accuracy.
Because only English, Hindi and Telugu can be evaluated reliably, the system supports these three.

### 6.3 Calibration

| Temperature | Log-loss | Mean top probability |
|---|---|---|
| T = 1.0 (uncalibrated) | 4.561 | 0.980 |
| T = 15.5 (fitted) | 0.648 | 0.727 |

Actual accuracy on the same words is 0.751. After scaling, the mean top probability (0.727) is close
to the accuracy, whereas before scaling the model claimed 0.980.

### 6.4 Development set

Token accuracy 0.858 (95% bootstrap interval 0.806–0.904), macro-F1 0.852, switch precision 0.695,
recall 0.740, F1 0.717. Without the dictionary (n-gram only), accuracy is 0.805 and switch F1 is
0.659. 24 of the 169 tokens were wrong.

### 6.5 Context-smoothing experiment

Each word is currently classified alone. To test whether neighbours help, a Viterbi decoding step
was added: every token gets a probability distribution over the three languages, and the best
language sequence is chosen with a penalty for changing language between neighbours. Two settings
(the switch probability and the dictionary confidence) were tuned on the development set by grid
search (7 × 4 combinations).

The best setting changed macro-F1 from 0.852 to 0.859 and left accuracy unchanged at 0.858, while
switch F1 went from 0.717 to 0.715; stronger smoothing lowered scores (for example accuracy 0.751 at
a switch probability of 0.2). One reason is that the development sentences switch language between
about 57% of neighbouring words (77 switches across 136 word pairs), so a prior that favours staying
in the same language fits the data poorly. The step was therefore left **disabled**, and the model
was frozen without it.

### 6.6 Test set (single run)

Token accuracy **0.877** (95% bootstrap interval 0.840–0.911), macro-F1 0.875.

| Language | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| English | 0.816 | 0.991 | 0.895 | 112 |
| Hindi | 0.899 | 0.832 | 0.864 | 107 |
| Telugu | 0.951 | 0.794 | 0.865 | 97 |

Confusion matrix (rows = gold, columns = predicted):

| | en | hi | te |
|---|---|---|---|
| en | 111 | 0 | 1 |
| hi | 15 | 89 | 3 |
| te | 10 | 10 | 77 |

Accuracy by decision method:

| Decision method | Tokens | Accuracy |
|---|---|---|
| Script rule | 19 | 1.000 |
| Dictionary only | 119 | 0.916 |
| Dictionary + n-gram | 143 | 0.825 |
| n-gram only | 35 | 0.886 |

### 6.7 Switch detection

A predicted switch counts as correct only if both its position and its language pair match a gold
switch.

| Measure | Value |
|---|---|
| Gold / predicted / matched switches | 147 / 142 / 111 |
| Precision / recall / F1 | 0.782 / 0.755 / 0.768 |
| Sentences with exactly the right switch count | 0.657 |
| Sentences with exactly the right language sequence | 0.600 |
| Mean absolute error in switch count per sentence | 0.443 |

### 6.8 Ablation

| Configuration | Token accuracy | Macro-F1 | Switch F1 |
|---|---|---|---|
| Dictionary + n-gram (final system) | 0.877 | 0.875 | 0.768 |
| n-gram model only | 0.839 | 0.837 | 0.726 |

The dictionary raises accuracy by about four points and switch F1 by about four points. (On the test
set, the context step is disabled, so the "with context" row is identical to the final system.)

---

## 7. Error analysis

The final system made 39 errors on 316 scored tokens. Grouping them by how they were decided
(counted from the saved error list):

| Cause | Errors | Description |
|---|---|---|
| Word listed under several languages | 25 | The classifier had to choose between languages without context. |
| Dictionary listed the word under only one (wrong) language | 10 | The single-language dictionary match was wrong. |
| Word not in the dictionary | 4 | The n-gram model alone decided and was wrong. |

Direction of errors: Telugu words labeled English (10) or Hindi (10); Hindi words labeled English (15)
or Telugu (3); one English word labeled Telugu.

**Cross-language homographs (25).** Short function words are spelled the same in several languages.
The Telugu dative suffix `ki` was labeled Hindi six times, because Hindi also has `ki`; `lo` (Telugu
"in") was labeled English three times; `ne`, `ho`, `do`, `Mera` and `Main` show the same pattern for
Hindi. A check of the English word list confirmed that ten such words (`ki`, `lo`, `tho`, `ga`,
`yeh`, `wo`, `ke`, `ho`, `aa`, `main`) appear in it.

**Misleading dictionary matches (10).** Some Hindi and Telugu words are in the English frequency list
as ordinary tokens, so they are listed only under English: Hindi `Yeh`, `Wo` (twice), `Hum`; Telugu
`Ee` (twice), `Aa`, `ga` (twice). The Telugu word `akali` ("hunger") was listed only under Hindi.

**Unlisted words (4).** The n-gram model alone mislabeled Telugu `chey` and Hindi `phans`, `yaad` and
`Arre`.

**Effect on switches.** A wrong label inside a run creates two extra switches or removes one, so
switch F1 (0.768) is lower than token accuracy (0.877).

**Possible remedies, not applied.** Curated function-word lists per language and a training corpus
of real code-switched text would address most of these errors. They were not added because the same
particles occur in the test set that had already been examined; adding them would make the test
result optimistic.

---

## 8. Implementation and interface

### 8.1 Backend

Python with scikit-learn and FastAPI. The model, dictionary and calibration temperature are saved
together and loaded once at server start. Endpoints:

- `GET /api/health` – status and active languages.
- `POST /api/analyze` – tokens with language, decision method and probability (when available), plus
  segments, switches, distribution, switch density, mixing index and least-certain tokens.
- `POST /api/compare` – the same analysis for two texts.

Unit tests check the analysis formulas against hand-computed values (the worked example in
Section 4.6, neutral tokens, ties, empty and single-token input, ordering of uncertain tokens).

### 8.2 Frontend

React with Tailwind CSS and Framer Motion. Views:

- **Language canvas:** the input as annotated text; each word has an underline and label in its
  language color and appears in sequence when the analysis completes.
- **Token inspector:** language, position, script, the decision method, and the model probability
  with the runner-up language when the classifier made the decision.
- **Code-switch markers and language-flow timeline:** switches appear as markers in the sentence and
  numbered markers between segment bars; selecting one shows the language pair, boundary words and
  position. Hovering a segment highlights its words, and selecting a word highlights its segment.
- **Language fingerprint:** token shares per language as a horizontal composition.
- **Analysis summary:** sequence, switch density, mixing index and neutral tokens with their formulas.
- **Model uncertainty:** the tokens with the smallest gap between the top two language probabilities.
- **Compare mode:** two texts analysed side by side with the same measures; hovering a word or bar
  highlights all words of that language in both texts.

Every displayed number comes from the API response. Probabilities are shown only for tokens the
classifier decided.

[Insert screenshots: language canvas, flow timeline, fingerprint, uncertainty list, compare mode.]

---

## 9. Limitations and threats to validity

- **No context:** each word is classified independently. Shared words are the main error source.
- **Small, hand-made evaluation set:** 70 test sentences, written to resemble casual messages and
  switching frequently, rather than sampled from natural text. Results may not transfer to real
  social-media data. The bootstrap interval reflects sentence sampling only.
- **Single annotator:** labels were not checked by a second independent annotator, so there is no
  agreement score.
- **Training data mismatch:** the classifier is trained on dictionary-style word lists but applied
  to casual spellings.
- **Limited languages:** only English, Hindi and Telugu are supported and evaluated. Romanized
  Urdu is indistinguishable from Hindi in this system.
- **Word-list noise:** the English frequency list contains some foreign words and names, and the
  Dakshina lists do not contain particles written as separate words.
- **Choices not tuned:** the n-gram range, smoothing constant and the 20,000-word cap are standard or
  practical choices, not tuned values.

---

## 10. Conclusion and future work

LexiSwitch identifies languages token by token in English–Hindi–Telugu text, derives switch points
and mixing statistics, and presents them through an interface that shows only computed results.
On a test set evaluated once, it reaches 0.877 token accuracy and 0.768 switch F1. The experiments
show that the dictionary helps, that calibration makes the probabilities usable, that adding similar
languages hurts word-level romanized identification, and that simple context smoothing did not help
on this data.

Future work: train a sequence model (HMM or CRF) on real code-switched corpora, add curated
function-word lists, build a larger multi-annotator test set from natural text, support more
languages with labeled evaluation data, and handle names and numbers explicitly.

---

## References

1. D. M. Bikel and I. Zitouni, *Multilingual Natural Language Processing Applications: From Theory to
   Practice*, Pearson.
2. T. Siddiqui and U. S. Tiwary, *Natural Language Processing and Information Retrieval*, Oxford
   University Press. [verify publisher and edition]
3. D. Jurafsky and J. H. Martin, *Speech and Language Processing*, Pearson / draft chapters online.
4. B. Roark et al., "Processing South Asian Languages Written in the Roman Script: the Dakshina
   Dataset," LREC 2020. [verify details and dataset license]
5. R. Speer, `wordfreq` (Python package). [verify citation format]
6. C. Guo, G. Pleiss, Y. Sun and K. Q. Weinberger, "On Calibration of Modern Neural Networks,"
   ICML 2017 (temperature scaling).
7. G. Guzmán et al., "Metrics for Modeling Code-Switching Across Corpora," Interspeech 2017
   (switch and mixing measures). [verify]
8. F. Pedregosa et al., "Scikit-learn: Machine Learning in Python," JMLR 12, 2011.

---

## Appendix A: Reproducing the results

```
python scripts\prepare_data.py
python scripts\train_model.py
python scripts\evaluate.py data\eval\dev.txt
python scripts\evaluate.py data\eval\test.txt
python scripts\train_model.py --langs en,bn,gu,hi,kn,ml,mr,pa,sd,si,ta,te,ur
```

Fixed settings: character n-grams 1–4 (`char_wb`), add-0.1 smoothing, uniform priors, 20,000 words per
language and form, group split with random seed 42, 10% held out, bootstrap with 1,000 resamples
(seed 42). Raw outputs of these runs are in the `docs/` folder.