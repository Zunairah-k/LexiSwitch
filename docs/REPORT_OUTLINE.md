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
inspecting the results. The identifier combines Unicode script rules, a dictionary with hand-written
function-word lists, a character n-gram Naive Bayes classifier with calibrated probabilities, and a
light context-smoothing step. The first version reached a token accuracy of 0.877 on a held-out test
set. Testing the interface revealed that Hindi words were often labeled English; after targeted
improvements, the final system reaches 0.943 token accuracy (95% bootstrap interval 0.913–0.969) and
a switch-point F1 of 0.904 on a second, fresh test set evaluated once after the model was frozen.
Remaining errors come mostly from short words shared between languages.

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
4. Evaluate the system honestly with a development set and separate test sets, using accuracy,
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
mixed. This project defines both explicitly (Section 4.7).

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

### 2.6 Sequence decoding

Labeling each word independently ignores its neighbours. A hidden-Markov-style decoder (the Viterbi
algorithm, covered with sequence labeling in Jurafsky and Martin) chooses the most probable language
sequence given per-word evidence and a cost for changing language between neighbours.

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
 → context smoothing (Viterbi)
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

Two corrections were added in the improvement phase (Section 6.5):

- **Function-word lists.** Short hand-written lists of Hindi and Telugu closed-class words
  (pronouns, postpositions, question words, auxiliaries, conjunctions, common adverbs; 208 entries
  in total) replace the dictionary entry for those words. This was needed because the English
  frequency list contains many romanized Hindi and Telugu function words, so the dictionary listed
  them as English.
- **Frequent English words.** The 300 most frequent English words are fixed as English, unless a
  function-word list says otherwise, so that "the", "at" or "but" cannot be pulled toward Hindi.

### 4.4 Character n-gram Naive Bayes

Features are character n-grams of length 1 to 4, computed on the word padded with spaces at both
ends. For a word w with n-gram counts c(g), the classifier scores each language L:

log P(L | w) ∝ log P(L) + Σ_g c(g) · log P(g | L),   with   P(g | L) = (count(g, L) + α) / (Σ_g′ count(g′, L) + α · |V|)

where α = 0.1 is the smoothing constant and |V| is the n-gram vocabulary size. Class priors are
uniform, because the language mix of real text is unknown. The n-gram range and α are standard
choices and were not tuned.

**English-bias offsets.** On held-out words the classifier leaned toward English (English recall
0.966 against Hindi recall 0.507). A per-language offset is added to the log-scores; the offsets
were fitted on held-out dictionary words to maximise macro-F1 (English −10.0, Hindi +2.5,
Telugu −4.0). Applied at full strength they over-corrected on real sentences, so the offsets are
multiplied by a scale chosen on the development set (final scale 0.25).

### 4.5 Calibration

The log-scores are divided by a temperature T, passed through a softmax, and renormalised over the
candidate languages for that token:

p(L | w) = softmax( (log P(L | w) + offset_L) / T ), restricted to the candidate languages.

T was chosen from 1.0 to 40.0 in steps of 0.5 to minimise log-loss on held-out romanized words
(final value T = 12.5). Probabilities are shown in the interface only for tokens the classifier
decided.

### 4.6 Context smoothing

Every token gets a probability distribution over the three languages: a script-rule token puts
almost all mass on its language; a dictionary-only match puts a fixed share (the dictionary
confidence, 0.9) on its language; a classifier token uses its calibrated probabilities. The Viterbi
algorithm then selects the language sequence that maximises the sum of log emission scores and log
transition scores, where staying in the same language has probability 1 − s and switching has
probability s split between the other languages. The switch prior s is 0.5 in the final system.
With s = 2/3 (three languages) this is identical to deciding every token independently.

### 4.7 Code-switch analysis

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
Σp² = 53/81 and M = (28/81) ÷ (2 · 53/81) = 28/106 ≈ 0.264. The first version of the system labeled
"mam" as Telugu, which produced 5 switches, density 0.625 and M = 0.40 for the same sentence; the
final system labels it English and produces the 3 switches above. One wrong token changes the switch
statistics a great deal, which is why switch detection is evaluated separately from token accuracy.

---

## 5. Data

### 5.1 Training data

- **Hindi and Telugu:** romanized and native-script words from the Dakshina lexicons, which pair
  native words with several attested Latin-script spellings and counts. For each language, up to
  20,000 romanized words and up to 20,000 native-script words are kept, ranked by attestation count.
- **English:** the 20,000 most frequent English words from the `wordfreq` package, including
  words with apostrophes.
- The three-language model trains on 100,000 words (English 20,000; Hindi 40,000; Telugu 40,000).
  The final dictionary holds 53,479 Latin-script words, of which 5,243 are listed under more than one
  language.
- Words for ten other languages were extracted from the same dataset and used only in the
  thirteen-language experiment.

The cap of 20,000 words per language and form is a design choice to keep the classes balanced.

### 5.2 Held-out dictionary words

For model diagnostics, 10% of words are held out with a **group split**: the Dakshina data contains
several romanizations of the same native word, so all spellings of one word are kept on the same
side of the split. This prevents a spelling in training from leaking its sibling spelling into the
held-out set. These words are also used to fit the bias offsets and the temperature, so scores on
them are not an independent test.

### 5.3 Evaluation sentences

Three sets of hand-labeled sentences, written to resemble casual mixed-language messages:

| Set | Sentences | Code-switched | Tokens (en / hi / te) | Gold switch points | Role |
|---|---|---|---|---|---|
| Development | 35 | 31 | 182 (70 / 60 / 52) | 83 | all design decisions |
| Test set 1 | 70 | 62 | 316 (112 / 107 / 97) | 147 | run once on the first version; later used for error analysis |
| Test set 2 | 50 | 45 | 280 (82 / 120 / 78) | 125 | run once on the final, frozen version |

Each sentence has one label per word: `en`, `hi`, `te`, or `other` (names, numbers and words from other
languages; not scored). The development set includes two sentences that failed when the interface
was tested by hand.

**Labeling rules.** A word is labeled by the language it belongs to in the sentence. English loanwords
inside Telugu or Hindi sentences ("assignment", "college", "mam") are English. Words valid in two
languages are labeled by meaning. Both languages are labeled whether typed in Latin or native
script.

### 5.4 Provenance and protocol

[State accurately how the evaluation sentences were produced. Suggested wording, edit to match what
actually happened: "The sentences were drafted with the help of an AI assistant and labeled word by
word. All labels were then reviewed by the author, and the Telugu labels were checked by ____."]

The protocol had two phases. In the first phase, the model was built using the development set and
test set 1 was run once. In the second phase, interface testing showed that Hindi words were often
labeled English. The model was improved using the development set only, frozen, and evaluated once
on test set 2, which did not exist during the improvements. Test set 1 was run again afterwards only
to show the change on the same sentences, and is labeled as no longer held out. All evaluation data
has a single annotator, which is a limitation (Section 9).

---

## 6. Experiments and results

### 6.1 Held-out dictionary words (first version, three languages)

On 6,021 held-out Latin-script words, the n-gram classifier alone reached accuracy 0.751.

| Language | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| English | 0.642 | 0.966 | 0.771 | 1,984 |
| Hindi | 0.858 | 0.507 | 0.638 | 2,066 |
| Telugu | 0.857 | 0.789 | 0.822 | 1,971 |

775 of the 2,066 Hindi words were labeled English: single words carry little evidence, and short
romanized Hindi spellings resemble English letter patterns. After the bias offsets (full strength,
fitted on these same words) accuracy is 0.776 and macro-F1 rises from 0.744 to 0.779.

### 6.2 Three languages versus thirteen

The same method trained on all thirteen languages (run before the bias offsets were added) gives
accuracy 0.502 on 25,866 held-out Latin-script words (an earlier run with a random instead of group
split gave 0.504, so the leak was small).

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
| T = 1.0 (uncalibrated) | 3.389 | 0.978 |
| T = 12.5 (fitted) | 0.590 | 0.747 |

Accuracy on the same words is 0.776, so after scaling the mean top probability is close to the
accuracy, whereas before scaling the model claimed 0.978. (The first version gave log-loss 4.561 →
0.648 at T = 15.5.)

### 6.4 First version on test set 1

Run once, before any improvement: token accuracy **0.877** (95% interval 0.840–0.911), macro-F1
0.875, switch F1 0.768. Hindi recall was 0.832, with 15 of the 18 Hindi errors labeled English.
Without the dictionary, accuracy was 0.839. 39 of 316 tokens were wrong.

### 6.5 Improvement phase

User testing of the interface showed Hindi words labeled English in most sentences (for example
"main", "ke", "bohot", "lag", "ho"). The error analysis (Section 7.1) showed the causes: short Hindi
function words listed as English in the frequency list, a general lean of the classifier toward
English, and words that exist in both languages. Three changes were made, all tuned on the
development set only:

1. Function-word lists and fixed frequent English words (Section 4.3).
2. English-bias offsets, with a scale chosen from {1, 0.75, 0.5, 0.25, 0}: scale 0.25 gave the best
   development macro-F1 (0.944, against 0.939 at full strength and 0.938 with no offsets).
3. Context smoothing, tuned over switch prior {0.6, 0.5, 0.4, 0.3} and dictionary confidence
   {0.8, 0.9, 0.95}, adopted only if it gained at least 0.01 macro-F1 on the development set.
   The best setting (0.5, 0.9) raised development macro-F1 from 0.944 to 0.968, so it was adopted.
   Performance was sensitive to the setting: at a switch prior of 0.4 development macro-F1 was 0.919.

Development set after the changes: accuracy 0.967 (95% interval 0.940–0.989), switch F1 0.951. These
numbers were used for tuning and are optimistic.

### 6.6 Final system on test set 2 (single run)

Token accuracy **0.943** (95% bootstrap interval 0.913–0.969), macro-F1 0.944.

| Language | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| English | 0.918 | 0.951 | 0.934 | 82 |
| Hindi | 0.949 | 0.925 | 0.937 | 120 |
| Telugu | 0.962 | 0.962 | 0.962 | 78 |

Confusion matrix (rows = gold, columns = predicted):

| | en | hi | te |
|---|---|---|---|
| en | 78 | 4 | 0 |
| hi | 6 | 111 | 3 |
| te | 1 | 2 | 75 |

Accuracy by decision method:

| Decision method | Tokens | Accuracy |
|---|---|---|
| Script rule | 12 | 1.000 |
| Dictionary only | 183 | 0.978 |
| Dictionary + n-gram | 67 | 0.866 |
| n-gram only | 18 | 0.833 |

### 6.7 Switch detection

A predicted switch counts as correct only if both its position and its language pair match a gold
switch.

| Measure | Test set 2 | Test set 1 (first version) |
|---|---|---|
| Gold / predicted / matched switches | 125 / 114 / 108 | 147 / 142 / 111 |
| Precision / recall / F1 | 0.947 / 0.864 / 0.904 | 0.782 / 0.755 / 0.768 |
| Sentences with exactly the right switch count | 0.760 | 0.657 |
| Sentences with exactly the right language sequence | 0.740 | 0.600 |
| Mean absolute error in switch count per sentence | 0.340 | 0.443 |

### 6.8 Ablation

| Configuration | Test set 2: accuracy / switch F1 | Test set 1 (no longer held out): accuracy / switch F1 |
|---|---|---|
| Final system (dictionary + n-gram + smoothing) | 0.943 / 0.904 | 0.943 / 0.877 |
| Without context smoothing | 0.954 / 0.906 | 0.949 / 0.875 |
| n-gram model only | 0.800 / 0.652 | 0.842 / 0.729 |

The dictionary and function-word lists give the largest gain (about 14 accuracy points on test set 2).
Context smoothing improved the development set but did not improve either test set: accuracy was
slightly lower with it and switch F1 about equal (smoothing raises switch precision and lowers switch
recall). Its benefit is therefore not established, and the model was kept as frozen rather than
changed after seeing test results.

### 6.9 Before and after on the same sentences

On the 70 sentences of test set 1, token accuracy went from 0.877 (first version, held out) to 0.943
(final version, no longer held out), and switch F1 from 0.768 to 0.877. This shows the direction of
the improvement, but not an unbiased size, because those sentences guided the changes. The unbiased
figure for the final system is test set 2.

---

## 7. Error analysis

### 7.1 First version (test set 1, 39 errors)

| Cause | Errors | Description |
|---|---|---|
| Word listed under several languages | 25 | The classifier had to choose without context. |
| Dictionary listed the word under only one (wrong) language | 10 | The single-language dictionary match was wrong. |
| Word not in the dictionary | 4 | The n-gram model alone decided and was wrong. |

Hindi and Telugu function words such as `ki`, `lo`, `ne`, `ho`, `Yeh`, `Wo`, `Hum` were labeled English
or the wrong Indian language. A check confirmed that ten such words (`ki`, `lo`, `tho`, `ga`, `yeh`,
`wo`, `ke`, `ho`, `aa`, `main`) were in the English word list. This analysis motivated Section 6.5.

### 7.2 Final version (test set 2, 16 errors of 280)

| Cause | Errors | Examples |
|---|---|---|
| Word listed under several languages (decided with the n-gram model) | 9 | English `gym`, `wifi`, `late`, `Thanks` labeled Hindi; Hindi `Maine`, `ne`, `main` labeled English; `Bhai` labeled Telugu; Telugu `ki` labeled Hindi |
| Dictionary or function-word list gave the wrong single language | 4 | Hindi `do` and `Is` labeled English (frequent English words); Hindi `lo` (as in "kar lo") labeled Telugu, and `baar` labeled Telugu |
| Word not in the dictionary | 3 | Hindi `chalogi`, Telugu `chestanu` and `vachav` |

Remaining errors are mostly short words that exist in several languages: `do`, `is`, `main` and `lo`
are common words in both English and Hindi or Telugu, and no word-level rule resolves them. Some are
side effects of the new rules (fixing very frequent English words as English costs Hindi `do` and
`Is`; the Telugu function word `lo` costs Hindi "lo"). English words labeled Hindi (`gym`, `wifi`,
`late`, `Thanks`) show that the Hindi side still pulls some English words that are rare in the English
list.

**Effect on switches.** A wrong label inside a run creates two extra switches or removes one, so
switch recall (0.864) is lower than token accuracy (0.943).

---

## 8. Implementation and interface

### 8.1 Backend

Python with scikit-learn and FastAPI. The model, dictionary, offsets and calibration temperature are
saved together and loaded once at server start. Endpoints:

- `GET /api/health` – status and active languages.
- `POST /api/analyze` – tokens with language, decision method and probability (when available), plus
  segments, switches, distribution, switch density, mixing index and least-certain tokens.
- `POST /api/compare` – the same analysis for two texts.

Unit tests check the analysis formulas against hand-computed values (the worked example in
Section 4.7, neutral tokens, ties, empty and single-token input, ordering of uncertain tokens).

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

- **Shared words:** short words valid in several languages are still the main error source, and
  context smoothing only partly helps.
- **Optimistic evaluation:** the development scores were used for tuning. Test set 2 shares
  vocabulary with the hand-written function-word lists because both came from the same author's
  knowledge, so 0.943 is probably higher than the accuracy on natural text.
- **Small, hand-made evaluation sets:** 50 to 70 sentences each, written to resemble casual messages
  and switching frequently, rather than sampled from natural text. The bootstrap interval reflects
  sentence sampling only.
- **Single annotator:** labels were not checked by a second independent annotator, so there is no
  agreement score.
- **Hand-written word lists:** the Hindi list was written for review by a Hindi speaker; the Telugu
  list has not been reviewed by a native speaker.
- **Smoothing is fragile:** its setting was tuned on 35 sentences, performance varied noticeably
  between neighbouring settings, and it did not improve the test sets.
- **Training data mismatch:** the classifier is trained on dictionary-style word lists but applied
  to casual spellings.
- **Limited languages:** only English, Hindi and Telugu are supported and evaluated. Romanized
  Urdu is indistinguishable from Hindi in this system.
- **Word-list noise:** the English frequency list contains some foreign words and names.
- **Choices not tuned:** the n-gram range, smoothing constant and the 20,000-word cap are standard or
  practical choices, not tuned values.

---

## 10. Conclusion and future work

LexiSwitch identifies languages token by token in English–Hindi–Telugu text, derives switch points
and mixing statistics, and presents them through an interface that shows only computed results.
The final system reaches 0.943 token accuracy and 0.904 switch F1 on a test set evaluated once.
The experiments show that the dictionary and function-word lists matter most, that calibration makes
the probabilities usable, that adding similar languages hurts word-level romanized identification,
and that testing the interface by hand exposed a weakness the first evaluation understated.

Future work: train a sequence model (HMM or CRF) on real code-switched corpora, replace the
hand-written word lists with data-driven ones, build a larger multi-annotator test set from natural
text, support more languages with labeled evaluation data, and handle names and numbers explicitly.

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
python scripts\tune.py
python scripts\evaluate.py data\eval\dev.txt
python scripts\evaluate.py data\eval\test2.txt
python scripts\train_model.py --langs en,bn,gu,hi,kn,ml,mr,pa,sd,si,ta,te,ur
```

Fixed settings: character n-grams 1–4 (`char_wb`), add-0.1 smoothing, uniform priors, 20,000 words per
language and form, group split with random seed 42, 10% held out, bootstrap with 1,000 resamples
(seed 42). Tuned settings (`backend/app/tuned_params.json`): bias scale 0.25, switch prior 0.5,
dictionary confidence 0.9. Raw outputs of these runs are in the `docs/` folder.