"""Project configuration: brand list, campaign keywords, secrets."""

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"


@dataclass(frozen=True)
class Brand:
    brand_id: str
    display_name: str
    channel_id: str
    handle: str
    exclude_from_sentiment: bool = False


def load_brands(path: Path = CONFIG_DIR / "brands.yaml") -> list[Brand]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))["brands"]
    return [Brand(**b) for b in raw]


def load_campaign_tags(path: Path = CONFIG_DIR / "campaign_tags.yaml") -> dict[str, list[str]]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["campaign_tags"]


def get_secret(name: str) -> str | None:
    """Read a secret from the environment (.env locally, Streamlit secrets in the cloud)."""
    load_dotenv(ROOT / ".env")
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st

        return st.secrets.get(name)
    except Exception:
        return None
