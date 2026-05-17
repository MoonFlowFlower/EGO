# Ego Handmade Operator Cut v1 - STATUS

## Current Milestone

- name: `operator_extracted_primitives_v1_candidate`
- owner: `Codex`
- state: `local_extracted_primitives_candidate_pass`
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
- core-memory write remains explicit-operator-gated; `ego-handmade-operator-permission-gates-v1` extends this from `/remember` to `/remember` plus `remember_note` with explicit latest-user memory intent
- algorithm inventory classifies old-system capabilities as `keep / rewrite / discard / reference-only`
- subject context is readonly candidate context, not a router, reply owner, state writer, or memory authority
- Dark Souls paraphrase suite has 20 cases and preserves one expected operator behavior
- diff review confirms no forbidden paths were modified by this cut

## Current Result

Local extracted-primitives candidate pass.

Evidence:

- `python3 -m py_compile Ego_handmade/agent_base.py Ego_handmade/memory_system.py Ego_handmade/primitives/subject_context.py Ego_handmade/primitives/evals.py Ego_handmade/primitives/runtime_gate.py` passed.
- `TMPDIR=/tmp python3 -m pytest -q Ego_handmade/tests/test_operator_cut.py Ego_handmade/tests/test_memory_system.py Ego_handmade/tests/test_extracted_primitives.py` passed: `23 passed`.
- `printf '你认为黑暗之魂如何\nexit\n' | AGENT_MEMORY=0 LLM_PROVIDER=none python3 Ego_handmade/agent_base.py` passed.
- `git diff --check -- Ego_handmade docs/codex/tasks/ego-handmade-operator-cut-v1` passed.
- `printf '/remember manual smoke marker: 中文记忆注入检查\n你好\nexit\n' | AGENT_MEMORY=1 python3 Ego_handmade/agent_base.py` passed.
- `printf '/memory_context\nexit\n' | AGENT_MEMORY=1 python3 Ego_handmade/agent_base.py` passed and showed the remembered Chinese note under candidate-local operator memory context.

Later permission-gate note:

- `ego-handmade-operator-permission-gates-v1` supersedes the earlier `/remember only` wording with an explicit operator memory-write gate: `/remember` or model-callable `remember_note` when the latest user message clearly asks the agent to remember something. This does not promote `Ego_handmade/memory` to repo authority.

New extracted-primitive outputs:

- `Ego_handmade/docs/ALGORITHM_INVENTORY.md` classifies old-system capabilities as `keep / rewrite / discard / reference-only`.
- `Ego_handmade/primitives/subject_context.py` injects readonly candidate subject context; it does not route, write state, write memory, or own visible replies.
- `Ego_handmade/primitives/evals.py` defines the 20-case Dark Souls paraphrase suite.
- `Ego_handmade/primitives/runtime_gate.py` records the candidate gate and claim-ceiling contract.
- The old `Planner.propose` fallback keyword shortcut for time questions was removed so fallback planning no longer routes before LLM drafting.

This remains local proof only. It proves only candidate-local operator memory and extracted-primitive wiring after the new checks pass. It does not replace the formal EGO mainline, does not create an OpenEmotion memory authority, and does not authorize demotion of `EgoCore`, `OpenEmotion`, or `ego_desktop_lab`.

## Next Gate

Run a five-scenario operator comparison across `Ego_handmade`, `ego_desktop_lab`, and current EgoCore/OpenEmotion before any demotion or migration plan.
