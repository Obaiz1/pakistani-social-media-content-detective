# NLP_BENCHMARK — Phase 9

**Run:** 2026-10-17 · **Labels:** `data/labels/labels_v1.csv` (n=250) · **Status:** PROVISIONAL: labels are Claude drafts, not yet verified by the owner

Label distribution: {'positive': 119, 'neutral': 88, 'negative': 43}. Language distribution: {'english': 159, 'roman_urdu': 60, 'other': 27, 'mixed': 3, 'urdu_script': 1}.

## Language ID (rule-based, `src/nlp/langid.py`)

Accuracy **0.872** on n=250.

| Language | precision | recall | support |
|---|---|---|---|
| english | 0.91 | 0.92 | 159 |
| mixed | 0.00 | 0.00 | 3 |
| other | 0.78 | 0.78 | 27 |
| roman_urdu | 0.94 | 0.82 | 60 |
| urdu_script | 1.00 | 1.00 | 1 |

## Sentiment (3 classes; macro-F1 is the selection metric)

| Model | Slice | n | macro-F1 | accuracy |
|---|---|---|---|---|
| nvidia:nvidia/nemotron-3-super-120b-a12b | all | 250 | 0.869 | 0.892 |
| cardiffnlp/twitter-xlm-roberta-base-sentiment | all | 250 | 0.819 | 0.852 |
| routed: EN→cardiff-roberta, RU/mixed→roman-urdu-xlmr | all | 250 | 0.786 | 0.828 |
| Khubaib01/roman-urdu-sentiment-xlm-r | all | 250 | 0.763 | 0.800 |
| cardiffnlp/twitter-roberta-base-sentiment-latest | all | 250 | 0.721 | 0.800 |
| vader | all | 250 | 0.602 | 0.672 |
| nvidia:nvidia/nemotron-3-super-120b-a12b | english | 159 | 0.865 | 0.899 |
| cardiffnlp/twitter-xlm-roberta-base-sentiment | english | 159 | 0.836 | 0.881 |
| cardiffnlp/twitter-roberta-base-sentiment-latest | english | 159 | 0.795 | 0.862 |
| routed: EN→cardiff-roberta, RU/mixed→roman-urdu-xlmr | english | 159 | 0.779 | 0.855 |
| Khubaib01/roman-urdu-sentiment-xlm-r | english | 159 | 0.724 | 0.805 |
| vader | english | 159 | 0.643 | 0.736 |
| nvidia:nvidia/nemotron-3-super-120b-a12b | mixed | 3 ⚠️ n<20 | 1.000 | 1.000 |
| cardiffnlp/twitter-roberta-base-sentiment-latest | mixed | 3 ⚠️ n<20 | 0.222 | 0.333 |
| cardiffnlp/twitter-xlm-roberta-base-sentiment | mixed | 3 ⚠️ n<20 | 0.222 | 0.333 |
| Khubaib01/roman-urdu-sentiment-xlm-r | mixed | 3 ⚠️ n<20 | 0.222 | 0.333 |
| routed: EN→cardiff-roberta, RU/mixed→roman-urdu-xlmr | mixed | 3 ⚠️ n<20 | 0.222 | 0.333 |
| vader | mixed | 3 ⚠️ n<20 | 0.167 | 0.333 |
| cardiffnlp/twitter-xlm-roberta-base-sentiment | other | 27 | 0.641 | 0.963 |
| cardiffnlp/twitter-roberta-base-sentiment-latest | other | 27 | 0.641 | 0.963 |
| routed: EN→cardiff-roberta, RU/mixed→roman-urdu-xlmr | other | 27 | 0.641 | 0.963 |
| nvidia:nvidia/nemotron-3-super-120b-a12b | other | 27 | 0.614 | 0.926 |
| Khubaib01/roman-urdu-sentiment-xlm-r | other | 27 | 0.585 | 0.889 |
| vader | other | 27 | 0.537 | 0.815 |
| nvidia:nvidia/nemotron-3-super-120b-a12b | roman_urdu | 60 | 0.850 | 0.850 |
| Khubaib01/roman-urdu-sentiment-xlm-r | roman_urdu | 60 | 0.765 | 0.767 |
| cardiffnlp/twitter-xlm-roberta-base-sentiment | roman_urdu | 60 | 0.754 | 0.750 |
| routed: EN→cardiff-roberta, RU/mixed→roman-urdu-xlmr | roman_urdu | 60 | 0.734 | 0.733 |
| cardiffnlp/twitter-roberta-base-sentiment-latest | roman_urdu | 60 | 0.563 | 0.600 |
| vader | roman_urdu | 60 | 0.455 | 0.467 |
| cardiffnlp/twitter-xlm-roberta-base-sentiment | urdu_script | 1 ⚠️ n<20 | 0.333 | 1.000 |
| Khubaib01/roman-urdu-sentiment-xlm-r | urdu_script | 1 ⚠️ n<20 | 0.333 | 1.000 |
| nvidia:nvidia/nemotron-3-super-120b-a12b | urdu_script | 1 ⚠️ n<20 | 0.333 | 1.000 |
| vader | urdu_script | 1 ⚠️ n<20 | 0.000 | 0.000 |
| cardiffnlp/twitter-roberta-base-sentiment-latest | urdu_script | 1 ⚠️ n<20 | 0.000 | 0.000 |
| routed: EN→cardiff-roberta, RU/mixed→roman-urdu-xlmr | urdu_script | 1 ⚠️ n<20 | 0.000 | 0.000 |

## Is `nvidia:nvidia/nemotron-3-super-120b-a12b` really better than `cardiffnlp/twitter-xlm-roberta-base-sentiment`? (paired bootstrap, 2,000 resamples)

| Slice | n | Δ macro-F1 (top − runner-up) | 95% CI |
|---|---|---|---|
| all | 250 | +0.051 | [-0.007, +0.116] (includes 0: not significant) |
| english | 159 | +0.029 | [-0.040, +0.098] (includes 0: not significant) |
| roman_urdu | 60 | +0.098 | [-0.026, +0.227] (includes 0: not significant) |

## Caveats

- Labels are drafts by Claude (an LLM) until the owner verifies them; an LLM judge may agree with LLM-drafted labels more than a human would.
- The NVIDIA LLM prompt contains the same labelling rubric the annotator used (questions → neutral, desire to buy → positive, praise + complaint → neutral); the local models don't see it.
- Urdu-script (n=1) and mixed (n=3) comments are too rare to evaluate.

Confusion matrices (rows = truth, cols = prediction; order positive, neutral, negative) are in `docs/nlp_benchmark.json`.

## Notes

- `cardiffnlp/twitter-roberta-base-sentiment-latest`: id2label={0: 'negative', 1: 'neutral', 2: 'positive'}
- `cardiffnlp/twitter-xlm-roberta-base-sentiment`: id2label={0: 'negative', 1: 'neutral', 2: 'positive'}
- `Khubaib01/roman-urdu-sentiment-xlm-r`: id2label={0: 'Positive', 1: 'Negative', 2: 'Neutral'}
