#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys

from route_convergence_common import (
    HYGIENE_RULES,
    REPO_HYGIENE_POLICY_PATH,
    REPO_SURFACE_MAP_PATH,
    TASK_LANE_INDEX_PATH,
    build_route_entries,
    load_program_state,
    render_repo_hygiene_policy,
    render_repo_surface_map,
    render_task_lane_index,
)


def _git_lines(args: list[str]) -> list[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=REPO_HYGIENE_POLICY_PATH.parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _check_generated_file(path, expected: str, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"missing generated file: {path}")
        return
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        errors.append(f"generated file drift detected: {path}")


def main() -> int:
    errors: list[str] = []
    program_state = load_program_state()
    entries = build_route_entries(program_state)
    expected_lane_index = render_task_lane_index(program_state)
    expected_hygiene_policy = render_repo_hygiene_policy()
    expected_surface_map = render_repo_surface_map()

    _check_generated_file(TASK_LANE_INDEX_PATH, expected_lane_index, errors)
    _check_generated_file(REPO_HYGIENE_POLICY_PATH, expected_hygiene_policy, errors)
    _check_generated_file(REPO_SURFACE_MAP_PATH, expected_surface_map, errors)

    active_default_entries = [entry for entry in entries if entry.lane == "active_default"]
    if len(active_default_entries) != 1:
        errors.append(f"expected exactly one active_default entry, found {len(active_default_entries)}")
    elif active_default_entries[0].key != "ego-operator-human-operator-trial-v2":
        errors.append("active_default entry must be `ego-operator-human-operator-trial-v2` during EgoOperator human-observation gate")

    foundation_entries = [entry for entry in entries if entry.key == "ego-k0-foundation-001a"]
    if len(foundation_entries) != 1:
        errors.append(f"expected exactly one Foundation route entry, found {len(foundation_entries)}")
    else:
        foundation_entry = foundation_entries[0]
        if foundation_entry.lane != "closed_evidence":
            errors.append("Foundation must appear only in `closed_evidence`")
        foundation_why = foundation_entry.why.lower()
        required_foundation_semantics = (
            "bounded engineering evidence",
            "banked/accepted",
            "authorization consumed",
            "disabled",
            "non-mainline",
            "no runtime authority",
        )
        for phrase in required_foundation_semantics:
            if phrase not in foundation_why:
                errors.append(f"Foundation route explanation missing `{phrase}`")

    supporting_foundation_entries = [
        entry for entry in entries if entry.key == "ego-k0-foundation-001a" and entry.lane == "supporting_active"
    ]
    if supporting_foundation_entries:
        errors.append("Foundation must not appear in `supporting_active`")

    reference_kernel_entries = [entry for entry in entries if entry.key == "ego-k0-reference-kernel-001a"]
    if len(reference_kernel_entries) != 1:
        errors.append(f"expected exactly one Reference Kernel route entry, found {len(reference_kernel_entries)}")
    else:
        reference_kernel_entry = reference_kernel_entries[0]
        if reference_kernel_entry.lane != "parked":
            errors.append("Reference Kernel must appear only in `parked`")
        reference_why = reference_kernel_entry.why.lower()
        required_reference_semantics = (
            "foundation accepted",
            "h0 closed pre-run and not_tested",
            "all children false",
            "operator replace-versus-close decision pending",
        )
        for phrase in required_reference_semantics:
            if phrase not in reference_why:
                errors.append(f"Reference Kernel route explanation missing `{phrase}`")

    workstreams = {item.get("id"): item for item in program_state.get("workstreams") or []}
    active_ws = workstreams.get("ego_operator_first_transition") or {}
    if not active_ws:
        errors.append("ego_operator_first_transition workstream missing from docs/PROGRAM_STATE_UNIFIED.yaml")
    elif not str(active_ws.get("status") or "").strip():
        errors.append("ego_operator_first_transition workstream must carry a non-empty current status")
    supporting_ws = workstreams.get("repo_cleanup_route_convergence") or {}
    if supporting_ws.get("status") != "supporting_active":
        errors.append("repo_cleanup_route_convergence workstream must exist and stay `supporting_active`")

    foundation_ws = workstreams.get("k0_developmental_kernel_dual_track") or {}
    expected_foundation_status = (
        "foundation_engineering_accepted_bounded__authorization_consumed__"
        "operator_decision_required__runtime_disabled__non_mainline"
    )
    if foundation_ws.get("status") != expected_foundation_status:
        errors.append("K0 Foundation workstream must record bounded acceptance and consumed authorization")
    if foundation_ws.get("evidence_level") != "E3" or foundation_ws.get("verification_level") != "V3":
        errors.append("K0 Foundation workstream must retain the bounded Ego E3/V3 governance classification")
    if foundation_ws.get("enabled") is not False or foundation_ws.get("mainline_connected") is not False:
        errors.append("K0 Foundation workstream must remain disabled and non-mainline")

    foundation_sink_text = " ".join(
        (
            str(foundation_ws.get("status") or ""),
            str(foundation_ws.get("summary") or ""),
            foundation_entries[0].why if len(foundation_entries) == 1 else "",
        )
    ).lower()
    for stale_phrase in ("authorized_ready_to_implement", "authorized only"):
        if stale_phrase in foundation_sink_text:
            errors.append(f"stale Foundation authorization semantics remain: `{stale_phrase}`")

    gitignore_text = (REPO_HYGIENE_POLICY_PATH.parents[1] / ".gitignore").read_text(encoding="utf-8")

    for rule in HYGIENE_RULES:
        for snippet in rule.ignore_snippets:
            if snippet not in gitignore_text:
                errors.append(f".gitignore missing route-hygiene snippet `{snippet}`")

        untracked = _git_lines(["ls-files", "--others", "--exclude-standard", "--", rule.path_prefix])
        if untracked:
            errors.append(
                f"unignored operational exhaust present under {rule.path_prefix}: {', '.join(untracked[:5])}"
            )

        added = set(_git_lines(["diff", "--name-only", "--diff-filter=A", "HEAD", "--", rule.path_prefix]))
        added.update(_git_lines(["diff", "--cached", "--name-only", "--diff-filter=A", "--", rule.path_prefix]))
        if added:
            errors.append(
                f"new tracked operational exhaust detected under {rule.path_prefix}: {', '.join(sorted(added)[:5])}"
            )

    if errors:
        print(json.dumps({"status": "fail", "errors": errors}, ensure_ascii=False, indent=2))
        return 1

    print(
        json.dumps(
            {
                "status": "pass",
                "active_default": active_default_entries[0].key if active_default_entries else None,
                "supporting_active_count": sum(1 for entry in entries if entry.lane == "supporting_active"),
                "route_index": str(TASK_LANE_INDEX_PATH.relative_to(REPO_HYGIENE_POLICY_PATH.parents[1])),
                "hygiene_policy": str(REPO_HYGIENE_POLICY_PATH.relative_to(REPO_HYGIENE_POLICY_PATH.parents[1])),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
