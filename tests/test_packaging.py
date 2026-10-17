"""Guard: every runtime dependency in pyproject.toml must be in requirements.txt (Streamlit Cloud installs from it)."""

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _name(spec: str) -> str:
    return re.split(r"[<>=!~\[; ]", spec, maxsplit=1)[0].strip().lower().replace("_", "-")


def test_requirements_txt_covers_runtime_dependencies():
    deps = {_name(d) for d in tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["dependencies"]}
    reqs = {_name(line) for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
            if line and not line.startswith(("#", " "))}
    missing = deps - reqs
    assert not missing, f"regenerate requirements.txt (uv export ...): missing {sorted(missing)}"


def test_heavy_nlp_packages_stay_out_of_the_deployed_app():
    reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    for heavy in ("torch==", "transformers==", "bertopic=="):
        assert heavy not in reqs, f"{heavy} would bloat the Streamlit Cloud deploy"
