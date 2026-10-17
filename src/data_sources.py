"""Loaders for the datasets the app can display."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

SYNTHETIC_DIR = Path(__file__).resolve().parent.parent / "data" / "synthetic_demo"


@dataclass(frozen=True)
class Dataset:
    channels: pd.DataFrame
    videos: pd.DataFrame
    comments: pd.DataFrame


def load_synthetic_fixture(directory: Path = SYNTHETIC_DIR) -> Dataset:
    """Load the committed SYNTHETIC demo dataset (never real measurements)."""
    return Dataset(
        channels=pd.read_csv(directory / "channels.csv"),
        videos=pd.read_csv(directory / "videos.csv", parse_dates=["published_at_utc"]),
        comments=pd.read_csv(directory / "comments.csv", parse_dates=["published_at_utc"]),
    )
