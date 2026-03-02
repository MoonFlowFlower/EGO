import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.rollout_v0 import run_rollout, simulate_strategy, rank_results


def base_cfg(seed=42):
    return {
        "seed": seed,
        "k_steps": 6,
        "strategies": ["repair", "boundary", "withdraw"],
        "initial_state": {
            "energy": 0.7,
            "safety_stress": 0.4,
            "focus_fatigue": 0.3,
            "bond": 0.5,
            "trust": 0.5,
            "grudge": 0.2,
            "novelty_need": 0.5,
        },
        "other_minds_state": {
            "reliability": 0.6,
            "cooperativeness": 0.6,
            "attentiveness": 0.6,
        },
    }


# 1
def test_reproducible_same_seed():
    a = run_rollout(base_cfg(123))
    b = run_rollout(base_cfg(123))
    assert a == b


# 2
def test_different_seed_changes_output():
    a = run_rollout(base_cfg(123))
    b = run_rollout(base_cfg(124))
    assert a != b


# 3
def test_output_contract_fields():
    out = run_rollout(base_cfg())
    assert out["diagnostic_only"] is True
    assert out["side_effects"] == "none"
    assert "rankings" in out and "details" in out


# 4-6
@pytest.mark.parametrize("metric", ["by_persistence_cost", "by_info_gain", "by_risk"])
def test_rankings_have_all_strategies(metric):
    out = run_rollout(base_cfg())
    ranked = out["rankings"][metric]
    assert sorted([x["strategy"] for x in ranked]) == ["boundary", "repair", "withdraw"]


# 7
def test_relationship_ranking_exists():
    out = run_rollout(base_cfg())
    assert "by_relationship_change" in out["rankings"]


# 8-10
@pytest.mark.parametrize("strategy", ["repair", "boundary", "withdraw"])
def test_simulate_strategy_shape(strategy):
    cfg = base_cfg()
    out = simulate_strategy(strategy, cfg["k_steps"], cfg["seed"], cfg["initial_state"], cfg["other_minds_state"])
    assert out["strategy"] == strategy
    assert len(out["trajectory"]) == cfg["k_steps"]
    assert set(out["averages"].keys()) == {"risk", "persistence_cost", "info_gain", "relationship_change"}


# 11-13
@pytest.mark.parametrize("k_steps", [5, 7, 10])
def test_k_step_respected(k_steps):
    cfg = base_cfg()
    cfg["k_steps"] = k_steps
    out = run_rollout(cfg)
    assert all(d["k_steps"] == k_steps for d in out["details"])


# 14
def test_risk_in_0_1():
    out = run_rollout(base_cfg())
    for d in out["details"]:
        assert 0.0 <= d["averages"]["risk"] <= 1.0


# 15
def test_persistence_cost_in_0_1():
    out = run_rollout(base_cfg())
    for d in out["details"]:
        assert 0.0 <= d["averages"]["persistence_cost"] <= 1.0


# 16
def test_info_gain_in_0_1():
    out = run_rollout(base_cfg())
    for d in out["details"]:
        assert 0.0 <= d["averages"]["info_gain"] <= 1.0


# 17
def test_rank_sorting_persistence_monotonic():
    out = run_rollout(base_cfg())
    vals = [x["persistence_cost"] for x in out["rankings"]["by_persistence_cost"]]
    assert vals == sorted(vals)


# 18
def test_rank_sorting_info_gain_monotonic():
    out = run_rollout(base_cfg())
    vals = [x["info_gain"] for x in out["rankings"]["by_info_gain"]]
    assert vals == sorted(vals, reverse=True)


# 19
def test_rank_sorting_risk_monotonic():
    out = run_rollout(base_cfg())
    vals = [x["risk"] for x in out["rankings"]["by_risk"]]
    assert vals == sorted(vals)


# 20
def test_stable_json_output_keys():
    out = run_rollout(base_cfg())
    txt = json.dumps(out, sort_keys=True)
    assert "\"diagnostic_only\": true" in txt


# 21
def test_cli_writes_output(tmp_path: Path):
    out_file = tmp_path / "rollout.json"
    cmd = [sys.executable, "scripts/rollout_v0.py", "--seed", "99", "--output", str(out_file)]
    subprocess.check_call(cmd, cwd=Path(__file__).parent.parent)
    data = json.loads(out_file.read_text())
    assert data["seed"] == 99


# 22
def test_cli_input_override(tmp_path: Path):
    in_file = tmp_path / "in.json"
    out_file = tmp_path / "out.json"
    in_file.write_text(json.dumps({"k_steps": 9, "strategies": ["withdraw", "repair"]}))
    cmd = [sys.executable, "scripts/rollout_v0.py", "--input", str(in_file), "--output", str(out_file)]
    subprocess.check_call(cmd, cwd=Path(__file__).parent.parent)
    data = json.loads(out_file.read_text())
    assert data["k_steps"] == 9
    assert data["strategies"] == ["withdraw", "repair"]


# 23
def test_rank_results_helper_deterministic():
    fake = [
        {"strategy": "a", "averages": {"persistence_cost": 0.2, "info_gain": 0.4, "risk": 0.3, "relationship_change": 0.1}},
        {"strategy": "b", "averages": {"persistence_cost": 0.1, "info_gain": 0.5, "risk": 0.2, "relationship_change": 0.2}},
    ]
    ranked = rank_results(fake)
    assert ranked["by_persistence_cost"][0]["strategy"] == "b"
    assert ranked["by_info_gain"][0]["strategy"] == "b"
