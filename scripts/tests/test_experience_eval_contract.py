from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "validate_experience_eval_contract.py"
spec = importlib.util.spec_from_file_location("validate_experience_eval_contract", MODULE_PATH)
validate_experience_eval_contract = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = validate_experience_eval_contract
spec.loader.exec_module(validate_experience_eval_contract)


def test_experience_eval_contract_is_valid() -> None:
    result = validate_experience_eval_contract.validate_sample_pack()

    assert result["status"] == "ok"
    assert result["case_count"] >= 20
    assert result["dimension_count"] == 7
    assert set(result["covered_dimensions"]) == validate_experience_eval_contract.REQUIRED_DIMENSIONS
    assert {
        "deterministic_local",
        "scripted_real_entry",
        "scripted_with_llm_judge",
        "human_required",
    }.issubset(result["covered_observation_classes"])
