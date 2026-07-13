"""Thin repository runner for the isolated outcome utility."""

from __future__ import annotations

import sys
from pathlib import Path

_PACKAGE_SRC = (
    Path(__file__).resolve().parents[1]
    / "packages"
    / "ego_outcome_utility"
    / "src"
)
sys.path.insert(0, str(_PACKAGE_SRC))

from ego_outcome_utility.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
