#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from h1_e4_sampling_common import (
    APPEARANCE_REPORT_JSON,
    APPEARANCE_REPORT_MD,
    FAILURES_TABLE_JSON,
    FAILURES_TABLE_MD,
    FROZEN_SAMPLE_MATRIX_PATH,
    PREFLIGHT_REPORT_JSON,
    SAMPLE_LEVEL_REPORT_JSON,
    SAMPLE_LEVEL_REPORT_MD,
    SAMPLE_MANIFEST_JSON,
    SAMPLE_MANIFEST_MD,
    build_appearance_payload,
    build_failures_payload,
    build_final_sample_report,
    build_sample_manifest_payload,
    load_frozen_sample_matrix,
    load_live_process_version,
    load_sample_bundles,
    read_json,
    rel_path,
    resolve_sampling_source_root,
    render_appearance_markdown,
    render_failures_markdown,
    render_final_sample_markdown,
    render_sample_manifest_markdown,
    write_json,
    write_text,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build H1 E4 sample reports from authority real_telegram bundles")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Optional source repo root for authority sample bundles. Defaults to the current clean-bind repo from preflight when available.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    sample_matrix = load_frozen_sample_matrix(FROZEN_SAMPLE_MATRIX_PATH)
    preflight_payload = read_json(PREFLIGHT_REPORT_JSON) if PREFLIGHT_REPORT_JSON.exists() else {
        "decision": "unknown",
        "generated_at": None,
    }
    source_root = resolve_sampling_source_root(
        explicit_repo_root=Path(args.repo_root) if args.repo_root else None,
        preflight_payload=preflight_payload,
    )
    live_process_version = load_live_process_version(
        source_root / "EgoCore" / "artifacts" / "proto_self_v2" / "LIVE_TELEGRAM_PROCESS_VERSION.json"
    )
    bundles = load_sample_bundles(
        source_root / "artifacts" / "telegram_real_mainline_v1" / "real_telegram"
    )
    manifest_payload = build_sample_manifest_payload(
        sample_matrix=sample_matrix,
        bundles=bundles,
        live_process_version=live_process_version,
    )
    appearance_payload = build_appearance_payload(manifest_payload)
    failures_payload = build_failures_payload(manifest_payload)
    final_payload = build_final_sample_report(
        preflight_payload=preflight_payload,
        manifest_payload=manifest_payload,
        appearance_payload=appearance_payload,
        failures_payload=failures_payload,
    )

    write_json(SAMPLE_MANIFEST_JSON, manifest_payload)
    write_text(SAMPLE_MANIFEST_MD, render_sample_manifest_markdown(manifest_payload))
    write_json(APPEARANCE_REPORT_JSON, appearance_payload)
    write_text(APPEARANCE_REPORT_MD, render_appearance_markdown(appearance_payload))
    write_json(FAILURES_TABLE_JSON, failures_payload)
    write_text(FAILURES_TABLE_MD, render_failures_markdown(failures_payload))
    write_json(SAMPLE_LEVEL_REPORT_JSON, final_payload)
    write_text(SAMPLE_LEVEL_REPORT_MD, render_final_sample_markdown(final_payload))

    print(f"source_repo_root={source_root}")
    print(f"manifest_json={rel_path(SAMPLE_MANIFEST_JSON)}")
    print(f"appearance_json={rel_path(APPEARANCE_REPORT_JSON)}")
    print(f"failures_json={rel_path(FAILURES_TABLE_JSON)}")
    print(f"sample_report_json={rel_path(SAMPLE_LEVEL_REPORT_JSON)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
