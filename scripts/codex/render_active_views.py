#!/usr/bin/env python3
"""Write or check every active Ego reader view from the local pinned mirror."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR.parent))

from codex.product_axis import (
    load_product_axis,
    load_source_pin,
    render_active_views,
    sync_pinned_itl_mirror,
)


ROOT = Path(__file__).resolve().parents[2]


def render(root: str | Path, *, check: bool = False) -> list[str]:
    repo = Path(root).resolve()
    views = render_active_views(load_product_axis(repo), load_source_pin(repo))
    drift: list[str] = []
    for relative, content in views.items():
        target = repo / relative
        if check:
            if not target.is_file() or target.read_text(encoding="utf-8") != content:
                drift.append(relative)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-from-itl")
    parser.add_argument("--source-commit")
    args = parser.parse_args(argv)
    if bool(args.sync_from_itl) != bool(args.source_commit):
        parser.error("--sync-from-itl and --source-commit are required together")
    if args.sync_from_itl:
        sync_pinned_itl_mirror(args.root, args.sync_from_itl, args.source_commit)
    drift = render(args.root, check=args.check)
    if drift:
        print("drift: " + ", ".join(drift))
        return 1
    print("active views exact" if args.check else "active views rendered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
