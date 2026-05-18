# EgoOperator Rename + Docs Reader Safety Pass v1 - STATUS

## Current Milestone

- name: `ego_operator_rename_docs_safety_v1`
- owner: `Codex`
- state: `local_transition_pass`
- type: `repo_transition`

## Authority Snapshot

- Current default lane: `ego_operator_first_transition`
- Current runtime path: `EgoOperator/`
- Former runtime path: `Ego_handmade/`
- Legacy reference path remains: `legacy/ego-pre-handmade-mainline/`

## Claim Boundary

This task can claim only `EgoOperator naming/docs safety transition recorded`. It does not prove stable real user benefit, runtime efficacy, live autonomy, durable long-term memory effectiveness, broader replacement success, or consciousness.

## Decisions

- `EgoOperator` is the mainline name for the operator-first route formerly called `Ego_handmade`.
- No tracked compatibility alias is kept for `Ego_handmade`.
- Historical task directory names that include `ego-handmade` remain unchanged as history.
- Reader safety is banner/cross-link only; historical evidence is not rewritten.
- Whole-directory `git mv Ego_handmade EgoOperator` was blocked by local OS permissions, so tracked source files were moved individually. The remaining local `Ego_handmade/` directory contains only untracked/ignored runtime artifacts and is not part of the staged transition.

## Evidence

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/memory_system.py EgoOperator/real_use_gate.py EgoOperator/human_operator_trial.py` - pass.
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests` - pass, `63 passed`.
- `python3 scripts/codex/generate_program_state_views.py` - regenerated program-state mirrors.
- `python3 scripts/codex/generate_route_convergence_views.py` - regenerated route/hygiene views.
- `python3 scripts/codex/check_program_state_integrity.py --skip-diff-check` - pass.
- `python3 scripts/codex/verify_route_convergence.py` - pass, active default `ego-operator-rename-docs-safety-v1`.
- `python3 scripts/codex/verify_mainline_clarity.py` - pass, active default `ego-operator-rename-docs-safety-v1`.
- `python3 -m py_compile scripts/codex/verify_mainline_clarity.py` - pass.
- `git diff --cached --check` - pass.
- `rg -n "Ego_handmade|ego_handmade" README.md AGENTS.md docs/MAINLINE_QUICKSTART.md docs/PROGRAM_STATE_UNIFIED.yaml docs/STATUS.md docs/REPO_SURFACE_MAP.md scripts/codex EgoOperator` - only explicit `formerly Ego_handmade` / rename-transition notes remain.
- `rg -n 'Current mainline: \`subject_system_v1_governed_proactivity\`|Keep \`subject_system_v1_governed_proactivity\` as the only active default lane' docs/codex/tasks/repo-mainline-clarity-v1 PROJECT_MEMORY.md docs/OVERALL_PROGRESS.md docs/CURRENT_PROJECT_LOGIC_FLOW.md docs/codex/README.md docs/CODEX_CLOSED_LOOP_SELF_REVIEW_WORKFLOW.md` - remaining claims are in pre-EgoOperator docs with reader-safety banners.

## Open Gate

- Real human continuous-use trial remains pending after this naming/docs safety transition.
