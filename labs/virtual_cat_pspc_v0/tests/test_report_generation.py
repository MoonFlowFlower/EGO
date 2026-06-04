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
        assert "trace_hash" in text
