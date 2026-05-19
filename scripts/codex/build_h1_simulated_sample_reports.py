#!/usr/bin/env python3
from __future__ import annotations

from h1_simulated_sampling_common import (
    APPEARANCE_REPORT_JSON,
    FAILURES_TABLE_JSON,
    SAMPLE_LEVEL_REPORT_JSON,
    SAMPLE_MANIFEST_JSON,
    SIMULATED_TELEGRAM_DIR,
    build_simulated_reports,
    rel_path,
    write_simulated_reports,
)


def main() -> int:
    payloads = build_simulated_reports()
    write_simulated_reports(payloads)
    print(f"sample_root={rel_path(SIMULATED_TELEGRAM_DIR)}")
    print(f"manifest_json={rel_path(SAMPLE_MANIFEST_JSON)}")
    print(f"appearance_json={rel_path(APPEARANCE_REPORT_JSON)}")
    print(f"failures_json={rel_path(FAILURES_TABLE_JSON)}")
    print(f"sample_report_json={rel_path(SAMPLE_LEVEL_REPORT_JSON)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
