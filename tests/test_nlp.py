"""NLP unit tests that need no model downloads (SYNTHETIC example strings)."""

import pandas as pd
import pytest

pytest.importorskip("sklearn", reason="install the nlp group: uv sync --group nlp")

from src.nlp.benchmark import benchmark_table, score  # noqa: E402
from src.nlp.langid import detect_language  # noqa: E402
from src.nlp.sentiment import normalize_label


@pytest.mark.parametrize("text,lang", [
    ("Beautiful collection, love it", "english"),
    ("yaar suit bohat cute hai lekin price zyada hai", "roman_urdu"),
    ("kya price hai", "roman_urdu"),
    ("بہت خوبصورت", "urdu_script"),
    ("❤️❤️❤️", "other"),
    ("https://example.com/x", "other"),
    ("", "other"),
    ("The dress is so nice but yeh bohat mehnga hai and the price is too high", "mixed"),
])
def test_detect_language(text, lang):
    assert detect_language(text) == lang


@pytest.mark.parametrize("raw,label", [("POSITIVE", "positive"), ("Negative", "negative"), ("neutral", "neutral"),
                                        ("mixed", "neutral"), ("LABEL_0", "negative"), ("LABEL_2", "positive"),
                                        ("pos", "positive")])
def test_normalize_label(raw, label):
    assert normalize_label(raw) == label


def test_score_hand_computed():
    s = score(["positive", "negative", "neutral", "positive"], ["positive", "positive", "neutral", "positive"])
    # per-class F1: pos 2/(2+.5*1)=0.8, neu 1.0, neg 0.0 -> macro 0.6
    assert s["macro_f1"] == pytest.approx(0.6) and s["accuracy"] == pytest.approx(0.75)
    assert s["confusion"] == [[2, 0, 0], [0, 1, 0], [1, 0, 0]]


def test_benchmark_table_slices_and_flags_small_n():
    labels = pd.DataFrame({"sentiment": ["positive"] * 25 + ["negative"] * 5,
                           "language": ["english"] * 25 + ["roman_urdu"] * 5})
    t = benchmark_table(labels, {"m": ["positive"] * 30})
    by = t.set_index("slice")
    assert by.loc["all", "n"] == 30 and by.loc["english", "accuracy"] == 1.0
    assert not by.loc["roman_urdu", "sufficient"]
