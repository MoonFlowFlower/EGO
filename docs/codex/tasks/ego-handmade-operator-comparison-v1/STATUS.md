# Ego Handmade Operator Comparison v1 - STATUS

## Current Milestone

- name: `operator_comparison_v1`
- owner: `Codex`
- state: `local_candidate_pass_reference_baseline_unavailable`
- type: `bounded_candidate`

## Current Authority Snapshot

- formal mainline remains `subject_system_v1_governed_proactivity`
- `Ego_handmade` is candidate-only
- `ego_desktop_lab` remains lab/reference harness
- no `EgoCore`, `OpenEmotion`, program-state, or evidence-ledger change is authorized

## Completion Criteria

- comparison harness runs the 20-case paraphrase gate
- comparison harness runs the 5 fixed operator scenarios
- report records baseline references without faking old-system execution
- targeted tests pass
- syntax checks pass
- generated comparison artifacts stay under ignored `Ego_handmade/artifacts/comparison/`
- diff review confirms no forbidden paths were modified

## Current Result

Local candidate comparison pass with reference baselines marked unavailable.

## Evidence

- `python3 -m py_compile Ego_handmade/agent_base.py Ego_handmade/memory_system.py Ego_handmade/operator_comparison.py Ego_handmade/primitives/subject_context.py Ego_handmade/primitives/evals.py Ego_handmade/primitives/runtime_gate.py` passed.
- `TMPDIR=/tmp python3 -m pytest -q Ego_handmade/tests/test_operator_cut.py Ego_handmade/tests/test_memory_system.py Ego_handmade/tests/test_extracted_primitives.py Ego_handmade/tests/test_operator_comparison.py` passed: `29 passed`.
- `python3 Ego_handmade/operator_comparison.py --out Ego_handmade/artifacts/comparison/latest` passed and wrote ignored JSON/Markdown reports.
- `printf '你认为黑暗之魂如何\nexit\n' | AGENT_MEMORY=0 LLM_PROVIDER=none python3 Ego_handmade/agent_base.py` passed.
- `git diff --check -- Ego_handmade docs/codex/tasks/ego-handmade-operator-comparison-v1` passed.

Comparison report summary:

- status: `local_candidate_pass_reference_baseline_unavailable`
- paraphrase gate: `20` cases, `pass`
- operator scenarios: `5 / 5` scored `7 / 7`
- baselines: `EgoCore/OpenEmotion` and `ego_desktop_lab` recorded as `baseline_unavailable`, not faked as executed comparison runs

This proves only the deterministic local `Ego_handmade` comparison harness and
candidate-local behavior. It does not prove superiority over old systems,
formal replacement, live runtime efficacy, or user benefit.

## Next Gate

Review the local candidate pass against human operator expectations. Only after
that, decide whether to open `ego-mainline-demotion-v1`.
