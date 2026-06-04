from pathlib import Path

from labs.virtual_cat_pspc_v0.run_experiments import run_experiments


def test_experiment_runner_writes_canonical_reports(tmp_path):
    summary = run_experiments(tmp_path, seeds=[101, 102, 103])

    expected = [
        "BASELINE_REPORT.md",
        "DANGER_GENERALIZATION_REPORT.md",
        "MEMORY_DELETION_ABLATION.md",
        "FROZEN_WORLD_MODEL_ABLATION.md",
        "FROZEN_SELF_MODEL_ABLATION.md",
        "NO_PREDICTION_ERROR_LEARNING_ABLATION.md",
        "REPLAY_DETERMINISM_REPORT.md",
        "ANTI_HARDCODING_AUDIT.md",
        "GENERALIZATION_MATRIX_REPORT.md",
    ]

    assert summary["overall_status"] == "E4_passed"
    for name in expected:
        report = Path(tmp_path) / name
        assert report.exists()
        text = report.read_text(encoding="utf-8")
        assert "## What It Proves" in text
        assert "## What It Does Not Prove" in text
        assert "## Failure Meaning" in text
        assert "## Rollback Note" in text
        assert "trace_hash" in text or name == "ANTI_HARDCODING_AUDIT.md"

    audit_json = Path(tmp_path) / "anti_hardcoding_audit.json"
    assert audit_json.exists()
    audit_text = (Path(tmp_path) / "ANTI_HARDCODING_AUDIT.md").read_text(encoding="utf-8")
    assert "- status: `pass`" in audit_text
    assert "object-name decision rule hits: `0`" in audit_text
    assert "## What It Proves" in audit_text
    assert "## What It Does Not Prove" in audit_text

    matrix_json = Path(tmp_path) / "generalization_matrix.json"
    assert matrix_json.exists()
    matrix_text = (Path(tmp_path) / "GENERALIZATION_MATRIX_REPORT.md").read_text(encoding="utf-8")
    assert "- status: `pass`" in matrix_text
    assert "cup, vase, bottle, tall_box" in matrix_text
    assert "## What It Proves" in matrix_text
    assert "## What It Does Not Prove" in matrix_text
