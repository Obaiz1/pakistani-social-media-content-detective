"""Exercise real native controls against the project's labeled synthetic fixture."""

import base64
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.ipc as arrow_ipc
import pytest
from streamlit.testing.v1 import AppTest

from src.app_data import Loaded, synthetic_dataset
from src.reporting.export import summary_tables
from src.ui import brand_label

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def synthetic_loaded():
    return Loaded(synthetic_dataset(), "synthetic", "2026-10-17")


def app_test(script, loaded):
    at = AppTest.from_file(str(ROOT / script), default_timeout=60)
    at.session_state["loaded"] = loaded
    at.run()
    assert not at.exception, at.exception
    return at


def assert_healthy(at):
    assert not at.exception, at.exception
    assert any("SYNTHETIC" in warning.value for warning in at.warning)


def trace_values(value):
    """Plotly supports both ordinary JSON lists and typed-array JSON."""
    if isinstance(value, dict) and "bdata" in value:
        return np.frombuffer(base64.b64decode(value["bdata"]), dtype=value["dtype"])
    return np.asarray(value)


def test_brand_metric_choices_update_plot_and_evidence_table(synthetic_loaded):
    at = app_test("views/brands.py", synthetic_loaded)
    videos = synthetic_loaded.data.videos
    videos = videos[~videos["low_reliability"] & ~videos["likely_promoted"]]
    choices = {
        "Engagement rate: (likes + comments) ÷ views": ("er_views", True),
        "Like rate: likes ÷ views": ("like_rate", True),
        "Views per subscriber": ("views_per_sub", False),
    }
    assert at.radio[0].options == list(choices)
    for label, (column, percentage) in choices.items():
        at.radio[0].set_value(label).run()
        assert_healthy(at)
        expected = videos.groupby("brand_id")[column].median()
        spec = json.loads(at.get("plotly_chart")[0].proto.spec)
        plotted = {
            row.split("  (n=", 1)[0]: float(value)
            for trace in spec["data"]
            for row, value in zip(trace["y"], trace_values(trace["x"]))
        }
        assert plotted == pytest.approx({brand_label(brand): float(value) for brand, value in expected.items()})
        fmt = (lambda value: f"{value:.2%}") if percentage else (lambda value: f"{value:.2f}")
        expected_display = {brand_label(brand): fmt(value) for brand, value in expected.items()}
        assert at.dataframe[0].value.set_index("Group")["Median"].to_dict() == expected_display


@pytest.mark.parametrize("key", ["f_brands", "f_buckets"])
def test_empty_filter_selections_show_informative_state(synthetic_loaded, key):
    at = app_test("views/overview.py", synthetic_loaded)
    at.multiselect(key=key).set_value([]).run()
    assert_healthy(at)
    assert any("No videos match the current filters" in info.value for info in at.info)
    assert not at.metric
    assert not at.get("plotly_chart")


def test_promoted_toggle_preserves_reliability_exclusion(synthetic_loaded):
    at = app_test("views/overview.py", synthetic_loaded)
    videos = synthetic_loaded.data.videos
    for include_promoted in (True, False):
        at.toggle(key="f_promo").set_value(include_promoted).run()
        assert_healthy(at)
        eligible = ~videos["low_reliability"]
        if not include_promoted:
            eligible &= ~videos["likely_promoted"]
        count = next(metric.value for metric in at.metric if metric.label == "Videos analysed")
        assert int(count.replace(",", "")) == int(eligible.sum())


def test_shared_filter_state_survives_page_navigation(synthetic_loaded):
    at = app_test("app.py", synthetic_loaded)
    selected_brand = at.multiselect(key="f_brands").value[0]
    selected_bucket = "16-30s"
    dates = sorted(synthetic_loaded.data.videos["published_at_pkt"].dt.date.unique())
    selected_dates = (dates[1], dates[-1])
    at.multiselect(key="f_brands").set_value([selected_brand])
    at.multiselect(key="f_buckets").set_value([selected_bucket])
    at.date_input(key="f_dates").set_value(selected_dates)
    at.toggle(key="f_promo").set_value(True)
    at.run()

    def assert_filters_retained():
        assert_healthy(at)
        assert at.session_state["f_brands"] == [selected_brand]
        assert at.session_state["f_buckets"] == [selected_bucket]
        assert at.session_state["f_dates"] == selected_dates
        assert at.session_state["f_promo"] is True
        assert at.session_state["loaded"].source == "synthetic"

    for page in ("views/brands.py", "views/content.py", "views/method.py", "views/overview.py"):
        at.switch_page(page).run()
        assert_filters_retained()
        if page != "views/method.py":
            assert at.multiselect(key="f_brands").value == [selected_brand]
            assert at.multiselect(key="f_buckets").value == [selected_bucket]
            assert at.date_input(key="f_dates").value == selected_dates
            assert at.toggle(key="f_promo").value is True

    for label, title in (("Explore content", "Content"), ("What to post next", "What to post next")):
        at.switch_page("views/overview.py").run()
        next(button for button in at.button if button.label == label).click().run()
        assert_filters_retained()
        assert at.title[0].value == title


def test_export_table_selector_and_unavailable_recommendation_download(synthetic_loaded, monkeypatch):
    observed = {}

    def observe_tables(*args, **kwargs):
        observed["tables"] = summary_tables(*args, **kwargs)
        return observed["tables"]

    monkeypatch.setattr("src.reporting.export.summary_tables", observe_tables)
    at = app_test("views/exports.py", synthetic_loaded)
    videos = synthetic_loaded.data.videos
    videos = videos[~videos["low_reliability"] & ~videos["likely_promoted"]]
    tables = summary_tables(videos, synthetic_loaded.data.comments, brand_label)
    assert at.selectbox[0].options == list(tables)
    for name, expected in tables.items():
        at.selectbox[0].select(name).run()
        assert_healthy(at)
        pd.testing.assert_frame_equal(at.dataframe[0].value, expected)
    downloads = {button.proto.label: button.proto.disabled for button in at.get("download_button")}
    assert downloads == {
        "⬇️ Excel workbook (all tables)": False,
        "⬇️ Recommendations (CSV)": True,
        "⬇️ PDF report": False,
    }
    at.multiselect(key="f_buckets").set_value(["61-180s"])
    at.toggle(key="f_promo").set_value(True)
    at.selectbox[0].select("Video length")
    at.run()
    assert_healthy(at)
    csv_download = next(button for button in at.get("download_button")
                        if button.proto.label == "⬇️ Recommendations (CSV)")
    assert csv_download.proto.disabled is False
    original = observed["tables"]["Video length"]
    assert np.isnan(original.attrs["kruskal_p"])
    pd.testing.assert_frame_equal(at.dataframe[0].value, original)
    proto = at.dataframe[0].proto
    arrow_bytes = getattr(proto, "arrow_data", proto).data
    arrow_table = arrow_ipc.open_stream(arrow_bytes).read_all()

    def reject_nonfinite(value):
        raise ValueError(f"Invalid JSON numeric token in browser table metadata: {value}")

    # The browser uses strict JSON.parse for pandas metadata. A NaN statistic in
    # DataFrame.attrs must stay in the scientific table, outside this payload.
    json.loads(arrow_table.schema.metadata[b"pandas"], parse_constant=reject_nonfinite)
