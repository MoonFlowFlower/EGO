# Ego Handmade Operator Permission Gates v1 - STATUS

## Current Milestone

- name: `operator_permission_gates_v1`
- owner: `Codex`
- state: `local_candidate_pass`
- type: `bounded_candidate`

## Current Authority Snapshot

- formal mainline remains `subject_system_v1_governed_proactivity`
- `Ego_handmade` is candidate-only
- no `EgoCore`, `OpenEmotion`, `ego_desktop_lab`, program-state, or
  evidence-ledger change is authorized

## Completion Criteria

- main agent exposes workspace-contained read tools by default
- side-effect tools remain env opt-in
- `remember_note` is exposed only with operator memory enabled
- core memory writes require explicit operator intent
- normal chat appends history without changing core memory
- targeted tests, syntax checks, and scoped diff check pass

## Current Result

Local permission-gate candidate pass.

## Evidence

- `python3 -m py_compile Ego_handmade/agent_base.py Ego_handmade/memory_system.py Ego_handmade/primitives/subject_context.py Ego_handmade/primitives/evals.py Ego_handmade/primitives/runtime_gate.py` passed.
- `TMPDIR=/tmp python3 -m pytest -q Ego_handmade/tests/test_operator_cut.py Ego_handmade/tests/test_memory_system.py Ego_handmade/tests/test_extracted_primitives.py Ego_handmade/tests/test_operator_comparison.py Ego_handmade/tests/test_permission_gates.py` passed: `38 passed`.
- `git diff --check -- Ego_handmade docs/codex/tasks/ego-handmade-operator-permission-gates-v1 docs/codex/tasks/ego-handmade-operator-cut-v1/acceptance.yaml docs/codex/tasks/ego-handmade-operator-cut-v1/STATUS.md` passed.
- CLI smoke: `printf '/tools\nexit\n' | AGENT_MEMORY=1 LLM_PROVIDER=none python3 Ego_handmade/agent_base.py` showed `remember_note`, read tools, operator memory enabled, and `write_file: disabled`.
- CLI smoke: `printf '普通中文闲聊\nexit\n' | AGENT_MEMORY=1 LLM_PROVIDER=none python3 Ego_handmade/agent_base.py` left existing `Ego_handmade/memory/MEMORY.md` hash unchanged while raw history append remained available.
- Manual fake-LLM smoke in a temporary containment root proved natural-language `remember_note` writes only with explicit memory intent, and `AGENT_ENABLE_WRITE_FILE` admits workspace writes while blocking `../` escape.

## Claim Boundary

This proves only `Ego_handmade local permission-gate candidate pass`. It does not
prove formal EGO mainline replacement, formal long-term memory efficacy, live
autonomy, runtime efficacy, stable user benefit, or consciousness.
