from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "analyze_functional_subject_repair_dependence.py"
spec = importlib.util.spec_from_file_location("analyze_functional_subject_repair_dependence", MODULE_PATH)
analyze_functional_subject_repair_dependence = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = analyze_functional_subject_repair_dependence
spec.loader.exec_module(analyze_functional_subject_repair_dependence)


def test_repair_dependence_audit_prioritizes_mechanism_critical_cases(tmp_path: Path) -> None:
    source = {
        "status": "scripted_functional_subject_judge_pass",
        "case_count": 4,
        "gpt55_judge": {"verdict": "pass"},
        "response_attribution_summary": {
            "schema_version": "ego_operator.response_attribution_summary.v1",
            "case_count": 4,
            "clean_first_pass_count": 1,
            "per_case": [
                {
                    "case_id": "fs_02_preference_change",
                    "origin": "runtime_repair",
                    "repair_types": ["boundary_quieting", "internal_mechanism_leak"],
                },
                {
                    "case_id": "fs_10_topic_switching",
                    "origin": "runtime_repair",
                    "repair_types": ["unbacked_memory_language", "topic_switching_continuity"],
                },
                {
                    "case_id": "fs_17_save_request",
                    "origin": "runtime_repair",
                    "repair_types": ["memory_save_success_terminal_reply"],
                },
                {
                    "case_id": "fs_14_paraphrase_stability",
                    "origin": "first_pass_llm",
                    "repair_types": [],
                },
            ],
        },
    }

    audit = analyze_functional_subject_repair_dependence.build_repair_dependence_audit(source, source_report="source.json")

    assert audit["status"] == "functional_subject_repair_dependence_audit_pass"
    assert audit["repair_case_count"] == 3
    assert audit["target_repair_case_count"] == 0
    assert [item["case_id"] for item in audit["priority_cases"]] == [
        "fs_02_preference_change",
        "fs_10_topic_switching",
        "fs_17_save_request",
    ]
    assert audit["checks"]["no_runtime_mutation_required"] is True
    assert audit["class_counts"]["visible_internal_context_leak"] == 1
    assert "runtime efficacy" in audit["not_claimed"]

    report_path = tmp_path / "source.json"
    report_path.write_text(json.dumps(source), encoding="utf-8")
    out = tmp_path / "out"
    written = analyze_functional_subject_repair_dependence.run(report_path=report_path, out_dir=out)
    assert written["status"] == "functional_subject_repair_dependence_audit_pass"
    assert (out / "functional_subject_repair_dependence_audit.json").exists()
    assert (out / "functional_subject_repair_dependence_audit.md").exists()
