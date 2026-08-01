from __future__ import annotations

import json
from pathlib import Path

from scripts.codex.run_ego_v2_public_acquisition_capacity_recovery_001k import (
    build_candidate_freeze,
    run_formal_packet,
)
from scripts.codex.verify_ego_v2_public_acquisition_capacity_recovery_001k import (
    run_positive_controls,
    verify_formal_packet,
)


ROOT = Path(__file__).resolve().parents[3]


def _tiny_formal_packet(tmp_path: Path) -> tuple[Path, Path, Path]:
    freeze_path = tmp_path / "candidate_freeze.json"
    build_candidate_freeze(
        ROOT,
        "S2_RISK_INFORMATION_GAIN",
        output_path=freeze_path,
    )
    output = tmp_path / "formal"
    run_formal_packet(
        ROOT,
        "qualification",
        output_root=output,
        freeze_path=freeze_path,
        test_only=True,
    )
    return (
        freeze_path,
        output / "qualification_result.json",
        output / "qualification_rows.jsonl",
    )


def test_independent_verifier_recomputes_tiny_formal_rows(tmp_path: Path) -> None:
    freeze_path, result_path, rows_path = _tiny_formal_packet(tmp_path)
    report = verify_formal_packet(
        ROOT,
        "qualification",
        result_path=result_path,
        rows_path=rows_path,
        freeze_path=freeze_path,
    )

    assert report["passed"] is True
    assert report["findings"] == []
    assert report["row_count"] == 144
    assert report["original_001j_packet_executed"] is False


def test_row_and_candidate_receipt_tamper_fail_closed(tmp_path: Path) -> None:
    freeze_path, result_path, rows_path = _tiny_formal_packet(tmp_path)
    rows = [json.loads(line) for line in rows_path.read_text(encoding="utf-8").splitlines()]
    public_index = next(
        index
        for index, row in enumerate(rows)
        if row["candidate_id"] == "S2_RISK_INFORMATION_GAIN" and row["ranked_tokens"]
    )
    rows[public_index]["deficit_loss"] = float(rows[public_index]["deficit_loss"]) + 0.1
    rows[public_index]["ranked_tokens"][0]["world_id"] = "leak"
    tampered = tmp_path / "tampered_rows.jsonl"
    tampered.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )

    report = verify_formal_packet(
        ROOT,
        "qualification",
        result_path=result_path,
        rows_path=tampered,
        freeze_path=freeze_path,
    )
    assert report["passed"] is False
    assert "rows_sha256_mismatch" in report["findings"]
    assert any(finding.startswith("trace_hash_mismatch") for finding in report["findings"])
    assert any(finding.startswith("ranked_token_private_field") for finding in report["findings"])


def test_formal_leakage_and_tamper_positive_controls_all_detect() -> None:
    report = run_positive_controls(ROOT)

    assert report["baseline_qualification_verifier_passed"] is True
    assert report["all_positive_controls_detected"] is True
    assert all(case["detected"] for case in report["cases"].values())
    assert report["original_001j_packet_executed"] is False
