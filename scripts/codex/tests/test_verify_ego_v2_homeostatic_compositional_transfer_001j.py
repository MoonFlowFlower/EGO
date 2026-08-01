from __future__ import annotations

import json
from pathlib import Path
import shutil

from scripts.codex.verify_ego_v2_homeostatic_compositional_transfer_001j import (
    verify_capacity_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
CANONICAL = REPO_ROOT / "artifacts" / "EGO-V2-HOMEOSTATIC-COMPOSITIONAL-TRANSFER-001J"


def _copy_packet(tmp_path: Path) -> Path:
    target = tmp_path / "packet"
    shutil.copytree(CANONICAL, target)
    return target


def test_canonical_negative_capacity_packet_is_independently_recomputed() -> None:
    report = verify_capacity_artifacts(CANONICAL)

    assert report["passed"] is True
    assert report["stored_verdict"] == "BENCHMARK_CAPACITY_NOT_ESTABLISHED"
    assert report["recomputed_verdict"] == report["stored_verdict"]
    assert report["heldout_rows"] == 0
    assert report["neural_candidate_source_present"] is False
    assert report["protected_predecessor_hashes_match"] is True


def test_capacity_verifier_rejects_row_tamper(tmp_path: Path) -> None:
    packet = _copy_packet(tmp_path)
    rows_path = packet / "capacity_rows.jsonl"
    rows = rows_path.read_text(encoding="utf-8").splitlines()
    first = json.loads(rows[0])
    first["deficit_loss"] = float(first["deficit_loss"]) + 0.25
    rows[0] = json.dumps(first, sort_keys=True, separators=(",", ":"))
    rows_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    report = verify_capacity_artifacts(packet)
    assert report["passed"] is False
    assert any("row" in finding or "manifest" in finding for finding in report["findings"])


def test_capacity_verifier_rejects_heldout_execution_alias(tmp_path: Path) -> None:
    packet = _copy_packet(tmp_path)
    rows_path = packet / "capacity_rows.jsonl"
    rows = rows_path.read_text(encoding="utf-8").splitlines()
    first = json.loads(rows[0])
    first["context_id"] = first["context_id"].replace("-dev-", "-heldout-")
    unsigned = {key: value for key, value in first.items() if key != "trace_hash"}
    from scripts.codex.check_ego_v2_homeostatic_compositional_transfer_001j_capacity import canonical_hash

    first["trace_hash"] = canonical_hash(unsigned)
    rows[0] = json.dumps(first, sort_keys=True, separators=(",", ":"))
    rows_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    report = verify_capacity_artifacts(packet)
    assert report["passed"] is False
    assert report["heldout_rows"] == 1
