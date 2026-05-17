# Ego Handmade Operator Cut v1 - STATUS

## Current Milestone

- name: `operator_memory_system_v1_candidate`
- owner: `Codex`
- state: `local_memory_system_candidate_pass`
- type: `bounded_candidate`

## Current Authority Snapshot

- formal mainline remains `subject_system_v1_governed_proactivity`
- `Ego_handmade` is candidate-only
- `ego_desktop_lab` remains lab/reference harness
- no `EgoCore`, `OpenEmotion`, program-state, or evidence-ledger change is authorized by this cut

## Completion Criteria

- targeted `Ego_handmade` tests pass
- syntax check passes for `Ego_handmade/agent_base.py`
- syntax check passes for `Ego_handmade/memory_system.py`
- memory artifacts stay under `Ego_handmade/memory/`
- `/remember` remains the only v1 direct core-memory write gate
- diff review confirms no forbidden paths were modified by this cut

## Current Result

Local memory-system candidate pass.

Evidence:

- `python3 -m py_compile Ego_handmade/agent_base.py Ego_handmade/memory_system.py` passed.
- `TMPDIR=/tmp python3 -m pytest -q Ego_handmade/tests/test_operator_cut.py Ego_handmade/tests/test_memory_system.py` passed: `16 passed`.
- `printf '/remember manual smoke marker: 中文记忆注入检查\n你好\nexit\n' | AGENT_MEMORY=1 python3 Ego_handmade/agent_base.py` passed.
- `printf '/memory_context\nexit\n' | AGENT_MEMORY=1 python3 Ego_handmade/agent_base.py` passed and showed the remembered Chinese note under candidate-local operator memory context.

This is local proof only. It proves only the candidate-local operator memory gate and artifact boundary. It does not replace the formal EGO mainline, does not create an OpenEmotion memory authority, and does not authorize demotion of `EgoCore`, `OpenEmotion`, or `ego_desktop_lab`.

## Next Gate

Run a five-scenario operator comparison across `Ego_handmade`, `ego_desktop_lab`, and current EgoCore/OpenEmotion before any demotion or migration plan.
