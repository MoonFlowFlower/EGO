#!/usr/bin/env python3
"""Compute the bounded route-closure verdict from live facts and artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


TASK_ID = "EGO-OUTCOME-UTILITY-ADAPTER-CLOSURE-001A"
ARTIFACT_DIR = Path(__file__).resolve().parent
ROOT = ARTIFACT_DIR.parents[1]
ITL_ROOT = ROOT.parent / "intelligence-theory-lab"
TASK_CARD = (
    ROOT
    / "docs"
    / "codex"
    / "tasks"
    / "ego-engineering-only-outcome-utility-route-replacement-001a"
    / "TASK-CARD-EGO-OUTCOME-UTILITY-ADAPTER-CLOSURE-001A.md"
)
MUTATION_SCOPE = TASK_CARD.parent / "CLOSURE_MUTATION_SCOPE.yaml"
FUNCTIONAL_CONTRACT = (
    ROOT
    / "docs"
    / "codex"
    / "tasks"
    / "ego-engineering-only-outcome-utility-route-replacement-001a"
    / "FUNCTIONAL_CONTRACT.json"
)
UTILITY_SOURCE = (
    ROOT
    / "packages"
    / "ego_outcome_utility"
    / "src"
    / "ego_outcome_utility"
    / "utility.py"
)
PARENT_RECORD = (
    ROOT.parent
    / "EGO-OUTCOME-UTILITY-SINGLE-OWNER-SHADOW-ADAPTER-ADMISSION-001A-CONTRACT.json"
)
EXPECTED_PARENT_VERDICT = "ADMISSION_DESIGN_BLOCKED__FEEDBACK_MAPPING_UNGROUNDED"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def git(repo: Path, *args: str, allowed: tuple[int, ...] = (0,)) -> str:
    completed = run(["git", "-C", str(repo), *args], repo)
    if completed.returncode not in allowed:
        raise RuntimeError(
            f"git {' '.join(args)} failed {completed.returncode}: {completed.stderr}"
        )
    return completed.stdout.rstrip("\n")


def git_grep(repo: Path, *args: str) -> list[str]:
    completed = run(["git", "-C", str(repo), "grep", *args], repo)
    if completed.returncode not in (0, 1):
        raise RuntimeError(
            f"git grep {' '.join(args)} failed {completed.returncode}: "
            f"{completed.stderr}"
        )
    return completed.stdout.rstrip("\n").splitlines() if completed.stdout else []


def head_blob_matches(path: Path) -> bool:
    relative = path.relative_to(ROOT).as_posix()
    completed = run(["git", "-C", str(ROOT), "show", f"HEAD:{relative}"], ROOT)
    if completed.returncode != 0:
        return False
    return hashlib.sha256(completed.stdout.encode("utf-8")).hexdigest() == sha256(path)


def normalize_section(text: str, start: str, end: str) -> str:
    body = text.split(start, 1)[1].split(end, 1)[0].strip()
    return " ".join(body.split())


def parse_reopen_conditions(card_text: str) -> list[str]:
    section = card_text.split("## 10. Reopen conditions", 1)[1].split(
        "Reopen never edits", 1
    )[0]
    items: list[str] = []
    current: list[str] = []
    for raw_line in section.splitlines():
        line = raw_line.strip()
        if line.startswith("- R"):
            if current:
                items.append(" ".join(current))
            current = [line[2:]]
        elif current and line:
            current.append(line)
    if current:
        items.append(" ".join(current))
    return items


def enabled_fields(value: Any, pointer: str = "") -> list[list[Any]]:
    found: list[list[Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_pointer = f"{pointer}/{key}"
            if key == "enabled":
                found.append([child_pointer, child])
            found.extend(enabled_fields(child, child_pointer))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(enabled_fields(child, f"{pointer}/{index}"))
    return found


def prior_record(path: Path, repo: Path) -> dict[str, str]:
    relative = path.relative_to(repo).as_posix()
    return {
        "repo": str(repo),
        "path": relative,
        "sha256": sha256(path),
        "last_commit": git(repo, "log", "-1", "--format=%H", "--", relative),
    }


def build_result() -> dict[str, Any]:
    code_path_hash = sha256(Path(__file__))
    card_text = TASK_CARD.read_text(encoding="utf-8")
    closure_path = ARTIFACT_DIR / "closure.md"
    closure_text = closure_path.read_text(encoding="utf-8")
    fact_path = ARTIFACT_DIR / "fact_grep_evidence.txt"
    annex_script = ARTIFACT_DIR / "power_annex.py"
    annex_path = ARTIFACT_DIR / "power_annex.json"
    annex_md_path = ARTIFACT_DIR / "power_annex.md"
    contract = json.loads(FUNCTIONAL_CONTRACT.read_text(encoding="utf-8"))
    parent = json.loads(PARENT_RECORD.read_text(encoding="utf-8"))

    ego_head = git(ROOT, "rev-parse", "HEAD")
    ego_tree = git(ROOT, "rev-parse", "HEAD^{tree}")
    ego_branch = git(ROOT, "branch", "--show-current")
    itl_head = git(ITL_ROOT, "rev-parse", "HEAD")
    itl_tree = git(ITL_ROOT, "rev-parse", "HEAD^{tree}")
    itl_status = git(ITL_ROOT, "status", "--porcelain=v1")

    source_calls = git_grep(
        ROOT,
        "-n",
        "-I",
        "-F",
        "observe_outcome(",
        "--",
        "*.py",
        ":(exclude)packages/ego_outcome_utility/**",
        ":(exclude)tests/test_ego_outcome_utility_001a.py",
        ":(exclude)artifacts/EGO-OUTCOME-UTILITY-ADAPTER-CLOSURE-001A/**",
    )
    documentation_signatures = git_grep(
        ROOT,
        "-n",
        "-I",
        "-F",
        "observe_outcome(",
        "--",
        "*.md",
        "*.json",
        "*.yaml",
        "*.yml",
        ":(exclude)artifacts/**",
        ":(exclude)docs/codex/tasks/ego-engineering-only-outcome-utility-route-replacement-001a/TASK-CARD-EGO-OUTCOME-UTILITY-ADAPTER-CLOSURE-001A.md",
    )
    ego_operator_imports = git_grep(
        ROOT, "-n", "-I", "-F", "ego_outcome_utility", "--", "EgoOperator"
    )
    ego_operator_output_refs: list[str] = []
    for term in (
        "observe_outcome",
        "outcome_micros",
        "ego.outcome_utility.prediction.v1",
    ):
        ego_operator_output_refs.extend(
            git_grep(ROOT, "-n", "-I", "-F", term, "--", "EgoOperator")
        )
    intervention_refs: list[str] = []
    for term in ("score_no_action", "epsilon-abstain", "epsilon_abstain"):
        intervention_refs.extend(
            git_grep(
                ROOT,
                "-n",
                "-I",
                "-F",
                term,
                "--",
                "packages/ego_outcome_utility",
                "EgoOperator",
                "scripts/run_ego_outcome_utility_001a.py",
            )
        )
    banked_parent_conflicts = git_grep(
        ROOT,
        "-n",
        "-I",
        "-F",
        "FEEDBACK_MAPPING_UNGROUNDED",
        "--",
        ".",
        ":(exclude)docs/codex/tasks/ego-engineering-only-outcome-utility-route-replacement-001a/TASK-CARD-EGO-OUTCOME-UTILITY-ADAPTER-CLOSURE-001A.md",
        ":(exclude)artifacts/EGO-OUTCOME-UTILITY-ADAPTER-CLOSURE-001A/**",
    )
    program_state_refs = git_grep(
        ROOT,
        "-n",
        "-I",
        "-E",
        "outcome.utility|outcome_micros|engineering.only.outcome",
        "--",
        "docs/PROGRAM_STATE_UNIFIED.yaml",
    )
    traffic_candidates = git(
        ROOT,
        "ls-files",
        "EgoOperator/**/*.jsonl",
        "EgoOperator/**/*.log",
        "EgoOperator/**/*trace*.json",
        "EgoOperator/**/*trial*.json",
    ).splitlines()

    runner_text = (ROOT / "scripts" / "run_ego_outcome_utility_001a.py").read_text(
        encoding="utf-8"
    )
    contract_enabled_fields = enabled_fields(contract)

    with tempfile.TemporaryDirectory(prefix="ego_closure_annex_recheck_") as temp:
        completed = run([sys.executable, str(annex_script), temp], ROOT)
        if completed.returncode != 0:
            raise RuntimeError(f"power annex recheck failed: {completed.stderr}")
        recheck_bytes = (Path(temp) / "power_annex.json").read_bytes()
    annex_bytes = annex_path.read_bytes()
    annex = json.loads(annex_bytes.decode("utf-8"))
    annex_double_run_identical = annex_bytes == recheck_bytes
    annex_hash = hashlib.sha256(annex_bytes).hexdigest()
    recheck_hash = hashlib.sha256(recheck_bytes).hexdigest()

    claim_ceiling = normalize_section(
        card_text,
        "## 9. Claim ceiling (verbatim in result.json and closure.md)",
        "## 10. Reopen conditions",
    )
    reopen_conditions = parse_reopen_conditions(card_text)

    gates = {
        "G1a_external_python_callers_zero": len(source_calls) == 0,
        "G1b_contract_enabled_false": bool(contract_enabled_fields)
        and all(item[1] is False for item in contract_enabled_fields),
        "G1b_explicit_cli_only": "from ego_outcome_utility.cli import main"
        in runner_text,
        "G1c_ego_operator_imports_zero": len(ego_operator_imports) == 0,
        "G1c_ego_operator_output_refs_zero": len(ego_operator_output_refs) == 0,
        "G1d_traffic_not_fabricated": (
            "traffic_fact: no qualifying tracked EgoOperator runtime decision logs; traffic unknown"
            in fact_path.read_text(encoding="utf-8")
            and "eligible decisions/day is unknown" in closure_text
            and "current_traffic_below_contour_claimed" not in closure_text
        ),
        "parent_external_verdict_matches": parent.get("verdict")
        == EXPECTED_PARENT_VERDICT,
        "parent_banked_conflict_absent": len(banked_parent_conflicts) == 0,
        "utility_intervention_path_absent": len(intervention_refs) == 0,
        "program_state_route_entry_absent": len(program_state_refs) == 0,
        "itl_untouched_clean": itl_status == "",
        "frozen_contract_unchanged_from_head": head_blob_matches(FUNCTIONAL_CONTRACT),
        "utility_source_unchanged_from_head": head_blob_matches(UTILITY_SOURCE),
        "G2_annex_double_run_identical": annex_double_run_identical,
        "G2_annex_source_hash_bound": annex.get("provenance", {}).get(
            "code_path_hash"
        )
        == sha256(annex_script),
        "G2_annex_input_hash_bound": annex.get("provenance", {})
        .get("input_artifacts", [{}])[0]
        .get("sha256")
        == sha256(annex_script),
        "G2_annex_rows_complete": len(annex.get("rows", [])) == 72,
        "G3_ground_a_present": "## Ground A" in closure_text,
        "G3_ground_b_present": "## Ground B" in closure_text,
        "G3_reopen_conditions_present": all(
            condition in " ".join(closure_text.split())
            for condition in reopen_conditions
        ),
        "G3_claim_ceiling_present": claim_ceiling
        in " ".join(closure_text.split()),
        "G4_positive_claim_false_authorized": "positive_claim=false" in closure_text,
        "G5_remote_anchor_forbidden": "Auto-Remote-Anchor: forbidden" in card_text,
        "G5_mutation_scope_forbids_push": "push: forbidden"
        in MUTATION_SCOPE.read_text(encoding="utf-8"),
    }
    failed_gates = sorted(key for key, passed in gates.items() if not passed)
    verdict = (
        "CLOSED_BY_BOUNDED_ANALYSIS" if not failed_gates else "CLOSURE_BLOCKED"
    )

    input_artifacts = {
        TASK_CARD.relative_to(ROOT).as_posix(): sha256(TASK_CARD),
        MUTATION_SCOPE.relative_to(ROOT).as_posix(): sha256(MUTATION_SCOPE),
        closure_path.relative_to(ROOT).as_posix(): sha256(closure_path),
        fact_path.relative_to(ROOT).as_posix(): sha256(fact_path),
        annex_script.relative_to(ROOT).as_posix(): sha256(annex_script),
        annex_path.relative_to(ROOT).as_posix(): annex_hash,
        annex_md_path.relative_to(ROOT).as_posix(): sha256(annex_md_path),
        FUNCTIONAL_CONTRACT.relative_to(ROOT).as_posix(): sha256(FUNCTIONAL_CONTRACT),
        UTILITY_SOURCE.relative_to(ROOT).as_posix(): sha256(UTILITY_SOURCE),
        str(PARENT_RECORD): sha256(PARENT_RECORD),
    }

    prior_negative_evidence = [
        prior_record(
            ITL_ROOT
            / "artifacts"
            / "UNCERTAINTY-VOI-REQUEST-MECHANISM-003A"
            / "result.json",
            ITL_ROOT,
        ),
        prior_record(
            ITL_ROOT
            / "artifacts"
            / "UNCERTAINTY-VOI-REQUEST-MECHANISM-003A"
            / "closure.json",
            ITL_ROOT,
        ),
        prior_record(
            ITL_ROOT
            / "docs"
            / "codex"
            / "contracts"
            / "LEARNING-SUCCESS-CRITERION-STANDARD-001A.md",
            ITL_ROOT,
        ),
        prior_record(
            ITL_ROOT
            / "docs"
            / "codex"
            / "contracts"
            / "BASELINE-IMMUNITY-ADMISSION-STANDARD-001A.md",
            ITL_ROOT,
        ),
        prior_record(
            ITL_ROOT
            / "docs"
            / "codex"
            / "contracts"
            / "MECHANISM-SIGNATURE-VERDICT-STANDARD-001A.md",
            ITL_ROOT,
        ),
        prior_record(
            ROOT
            / "artifacts"
            / "egodesktop_pet_world_integration_001a"
            / "p0"
            / "audit_claude_full_hostile_001.json",
            ROOT,
        ),
    ]

    result: dict[str, Any] = {
        "schema_version": "ego.outcome_utility.adapter_closure.result.v1",
        "task_id": TASK_ID,
        "verdict": verdict,
        "positive_claim": False,
        "route": "runtime_feedback_to_outcome_micros_admission",
        "layer": "engineering_implementation_plus_bounded_mechanism_governance",
        "mainline_integration_status": "absent",
        "enabled_status": "runtime_not_registered_explicit_local_cli_only",
        "real_trigger_evidence": "none_for_EgoOperator",
        "parent_verdict": EXPECTED_PARENT_VERDICT,
        "parent_record": {
            "provenance_class": "external_local_uncommitted",
            "path": str(PARENT_RECORD),
            "sha256": sha256(PARENT_RECORD),
            "parsed_verdict": parent.get("verdict"),
        },
        "grounds": [
            "A_counterfactual_unidentifiable_at_current_observational_access",
            "B_current_count_table_route_baseline_preempted",
        ],
        "facts": {
            "ego_head_sha": ego_head,
            "ego_tree_sha": ego_tree,
            "ego_branch": ego_branch,
            "itl_head_sha": itl_head,
            "itl_tree_sha": itl_tree,
            "package_dir": "packages/ego_outcome_utility",
            "package_import_name": "ego_outcome_utility",
            "observe_outcome_external_python_callers": len(source_calls),
            "documentation_signature_hits_not_callers": len(
                documentation_signatures
            ),
            "runtime_enable_flag_present": False,
            "functional_contract_enabled_fields": contract_enabled_fields,
            "mainline_consumers": 0,
            "utility_specific_intervention_paths": len(intervention_refs),
            "traffic_estimate": "no qualifying tracked EgoOperator runtime decision logs; traffic unknown",
            "traffic_candidate_file_count": len(traffic_candidates),
            "current_traffic_below_contour_claimed": False,
            "program_state_route_entry_present": False,
            "package_classification": contract.get("classification"),
        },
        "power_annex": {
            "producer_function": annex["provenance"]["producer_function"],
            "source_sha256": sha256(annex_script),
            "json_sha256": annex_hash,
            "recheck_json_sha256": recheck_hash,
            "double_run_identical": annex_double_run_identical,
            "row_count": len(annex["rows"]),
            "spot_checks": annex["spot_checks"],
            "reopen_contour": annex["reopen_contour"],
            "claim_boundary": "conditional analytic bound over declared assumptions; not measured traffic or product cost",
        },
        "baseline_results": {
            "executed": False,
            "status": "structural_identity_class_preemption_only",
            "strongest_control": "equal_access_context_action_count_table",
        },
        "ablation_results": {
            "executed": False,
            "status": "not_applicable_no_mechanism_run",
        },
        "replay_result": {
            "mechanism_replay_executed": False,
            "analytic_annex_recomputed_twice": True,
            "byte_identical": annex_double_run_identical,
        },
        "gates": gates,
        "stop_conditions_triggered": failed_gates,
        "prior_negative_evidence": prior_negative_evidence,
        "causal_ladder_provenance": "operator_standard_chat_provenance_2026-07-13",
        "reopen_conditions": reopen_conditions,
        "claim_ceiling": claim_ceiling,
        "auto_remote_anchor": "forbidden_pending_yellow_post_check",
        "producer_function": "build_closure_result.build_result",
        "input_artifacts": input_artifacts,
        "run_id": "ego-outcome-utility-adapter-closure-001a-result-v1",
        "seed_context_episode_ids": {
            "seed_ids": "NOT_APPLICABLE_NO_RNG",
            "context_ids": "NOT_APPLICABLE_ROUTE_CLOSURE",
            "episode_ids": "NOT_APPLICABLE_NO_EPISODES",
        },
        "aggregation_rule": "logical AND over named live-fact, source-integrity, parent, annex-recompute and closure-content gates",
        "code_path_hash": code_path_hash,
        "what_this_does_not_prove": (
            "No general utility impossibility, product non-need, measured traffic "
            "infeasibility, runtime learning, decision improvement, user value, "
            "mainline effect, agency, subjectivity or consciousness claim."
        ),
    }

    if failed_gates:
        failure = {
            "schema_version": "ego.outcome_utility.adapter_closure.failure.v1",
            "task_id": TASK_ID,
            "verdict": "CLOSURE_BLOCKED",
            "failed_gates": failed_gates,
            "gates": gates,
            "producer_function": "build_closure_result.build_result",
            "run_id": result["run_id"],
            "code_path_hash": code_path_hash,
        }
        (ARTIFACT_DIR / "failure_manifest.json").write_bytes(
            canonical_json_bytes(failure)
        )
        raise RuntimeError(f"closure gates failed: {failed_gates}")

    result_path = ARTIFACT_DIR / "result.json"
    result_path.write_bytes(canonical_json_bytes(result))
    return result


def main() -> int:
    result = build_result()
    result_path = ARTIFACT_DIR / "result.json"
    print(f"verdict={result['verdict']}")
    print(f"result_sha256={sha256(result_path)}")
    print(f"code_path_hash={result['code_path_hash']}")
    print(f"failed_gate_count={len(result['stop_conditions_triggered'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
