"""Phase 13 export tests (SYNTHETIC data): files open, contain aggregates only, carry caveats."""

import io

import pandas as pd
import pytest

from src.app_data import synthetic_dataset
from src.recommendations.engine import build_cards
from src.reporting.export import CAVEATS, latin1, pdf_report, summary_tables, to_excel_bytes

FORBIDDEN_COLUMNS = {"video_id", "title", "description", "text", "comment_id_hash", "channel_id"}


@pytest.fixture(scope="module")
def bundle():
    d = synthetic_dataset()
    v = d.videos[~d.videos["low_reliability"] & ~d.videos["likely_promoted"]]
    tables = summary_tables(v, d.comments)
    cards, _ = build_cards(v)
    meta = {"data source": "SYNTHETIC", "snapshot": "2026-10-17", "videos analysed": str(len(v))}
    return tables, cards, meta


def test_summary_tables_are_aggregates_only(bundle):
    tables, _, _ = bundle
    assert {"Brands (ER)", "Video length", "Campaign", "Weekday (PKT)"} <= set(tables)
    for name, t in tables.items():
        assert not (FORBIDDEN_COLUMNS & set(t.columns)), name
        assert (t["n"] > 0).all()


def test_excel_opens_with_about_sheet_and_caveats(bundle):
    xls = pd.ExcelFile(io.BytesIO(to_excel_bytes(*bundle)))
    assert xls.sheet_names[0] == "About" and "Video length" in xls.sheet_names
    about = xls.parse("About")
    assert set(CAVEATS) <= set(about["value"])
    assert "SYNTHETIC" in set(about["value"])


def test_pdf_is_valid_and_nonempty(bundle):
    data = pdf_report(*bundle)
    assert data[:5] == b"%PDF-" and len(data) > 3000


def test_pdf_handles_no_cards_and_unicode():
    tables = {"Brands (ER)": pd.DataFrame({"group": ["عید brand 🎯"], "n": [25], "median": [0.01], "ci_low": [0.008],
                                           "ci_high": [0.012]})}
    assert pdf_report(tables, [], {"note": "δ ≥ 0.147 – test"})[:5] == b"%PDF-"


def test_latin1_transliteration():
    assert latin1("Cliff's δ ≥ 0.15 – PKT 06–12 🎯") == "Cliff's delta >= 0.15 - PKT 06-12 "
