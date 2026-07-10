"""Explicit, side-effect-free-until-called utility CLI for canonical hashes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .contracts import canonical_hash


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-hash-json", type=Path, required=True)
    args = parser.parse_args(argv)
    value = json.loads(args.canonical_hash_json.read_text(encoding="utf-8"))
    print(canonical_hash(value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
