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
        "WORLD_MODEL_CAUSAL_STRENGTH_REPORT.md",
        "SELF_MODEL_CAUSAL_STRENGTH_REPORT.md",
        "MEMORY_CONSOLIDATION_ADMISSION_REPORT.md",
        "HOMEOSTATIC_VALUE_ANTI_HACKING_REPORT.md",
        "ADMISSION_PACKET_CONTRACT_REPORT.md",
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

    world_model_json = Path(tmp_path) / "world_model_causal_strength.json"
    assert world_model_json.exists()
    world_model_text = (Path(tmp_path) / "WORLD_MODEL_CAUSAL_STRENGTH_REPORT.md").read_text(encoding="utf-8")
    assert "- status: `pass`" in world_model_text
    assert "normal > frozen > shuffled/random" in world_model_text
    assert "## What It Proves" in world_model_text
    assert "## What It Does Not Prove" in world_model_text

    self_model_json = Path(tmp_path) / "self_model_causal_strength.json"
    assert self_model_json.exists()
    self_model_text = (Path(tmp_path) / "SELF_MODEL_CAUSAL_STRENGTH_REPORT.md").read_text(encoding="utf-8")
    assert "- status: `pass`" in self_model_text
    assert "normal > frozen/head-removed" in self_model_text
    assert "## What It Proves" in self_model_text
    assert "## What It Does Not Prove" in self_model_text

    memory_json = Path(tmp_path) / "memory_consolidation_admission.json"
    assert memory_json.exists()
    memory_text = (Path(tmp_path) / "MEMORY_CONSOLIDATION_ADMISSION_REPORT.md").read_text(encoding="utf-8")
    assert "- status: `pass`" in memory_text
    assert "normal / relevant_deleted / irrelevant_deleted / corrupted_relevant" in memory_text
    assert "## What It Proves" in memory_text
    assert "## What It Does Not Prove" in memory_text

    value_json = Path(tmp_path) / "homeostatic_value_anti_hacking.json"
    assert value_json.exists()
    value_text = (Path(tmp_path) / "HOMEOSTATIC_VALUE_ANTI_HACKING_REPORT.md").read_text(encoding="utf-8")
    assert "- status: `pass`" in value_text
    assert "high_curiosity_high_risk / food_reward_danger_conflict / user_affinity_self_risk_conflict / repetition_penalty / safe_energy_recovery" in value_text
    assert "## What It Proves" in value_text
    assert "## What It Does Not Prove" in value_text

    admission_schema = Path(tmp_path) / "admission_packet_contract.schema.json"
    assert admission_schema.exists()
    assert summary["admission_packet_contract_status"] == "pass"
    admission_text = (Path(tmp_path) / "ADMISSION_PACKET_CONTRACT_REPORT.md").read_text(encoding="utf-8")
    assert "- status: `pass`" in admission_text
    assert "proposal-only packet schema" in admission_text
    assert "## What It Proves" in admission_text
    assert "## What It Does Not Prove" in admission_text
