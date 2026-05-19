#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "EgoCore") not in sys.path:
    sys.path.insert(0, str(ROOT / "EgoCore"))
if str(ROOT / "OpenEmotion") not in sys.path:
    sys.path.insert(0, str(ROOT / "OpenEmotion"))

from app.dashboard.reply_sample_preflight import (
    render_reply_sample_preflight_markdown,
    run_reply_sample_preflight,
)


ARTIFACT_ROOT = ROOT / "artifacts" / "telegram_real_mainline_v1" / "dashboard_v1"
DEFAULT_JSON = ARTIFACT_ROOT / "UNIFIED_INGRESS_REPLY_SAMPLE_PREFLIGHT_CURRENT.json"
DEFAULT_MD = ARTIFACT_ROOT / "UNIFIED_INGRESS_REPLY_SAMPLE_PREFLIGHT_CURRENT.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run bounded dashboard unified-ingress reply-sample preflight")
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    parser.add_argument(
        "--session-prefix",
        default="reply-sample-preflight",
        help="Session-name prefix used for per-prompt dashboard chat sessions.",
    )
    return parser.parse_args()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    report = run_reply_sample_preflight(session_prefix=args.session_prefix)
    _write_json(args.output_json, report)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_reply_sample_preflight_markdown(report), encoding="utf-8")
    print(json.dumps(report.get("summary") or {}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
