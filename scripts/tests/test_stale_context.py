from __future__ import annotations

from scripts.codex.product_axis import render_active_views
from scripts.codex.stale_context import run_positive_controls, scan_active_views

from scripts.tests.test_product_axis import _axis


def test_live_generated_views_pass_stale_context_scanner() -> None:
    result = scan_active_views(render_active_views(_axis()), _axis())
    assert result.verdict == "pass"
    assert result.findings == ()


def test_positive_controls_use_production_scanner_and_all_trigger() -> None:
    report = run_positive_controls(_axis())
    assert report["verdict"] == "pass"
    assert report["producer_function"] == "run_positive_controls"
    assert set(report["cases"]) == {
        "old_active_owner",
        "entrypoint_drift",
        "source_pin_drift",
        "enablement_drift",
    }
    assert all(row["detected"] for row in report["cases"].values())
