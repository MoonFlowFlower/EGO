# Subjective Loop v1 Product Cut Report

## Summary

This cut consolidates `ego_desktop_lab` as a reference kernel / acceptance harness for the main EGO subjective loop. It does not make `ego_desktop_lab` a second product runtime.

The formal product direction remains:

`EgoCore ingress -> OpenEmotion subject loop -> EgoCore gate/output_check -> shell/Telegram visible response`

## Contract

New lab reference contract:

- `SubjectEvent`: user text, context, recent dialogue, and safety pre-route.
- `AffectiveAppraisal`: feedback signal, valence, arousal, repair need, trust delta, rationale.
- `SubjectDecision`: semantic understanding, affective appraisal, memory delta, intention proposal, gate decision, response plan, decision class.
- `SubjectEvidence`: before/after summaries, why selected, why blocked/asked, feedback outcome, claim ceiling.

## Milestone 1 Slice

Implemented behavior:

- Normal local commands still route through DecisionView.
- Feedback inputs such as `你误解了`, `这样不对`, `有帮助`, and `没帮助` generate a session-local feedback outcome.
- Negative feedback changes the next clarification response instead of repeating the same generic prompt.
- Affective grounding requires acknowledging possible misalignment before giving the next step.
- Mainline parity is tested at the decision-class level without changing EgoCore/OpenEmotion runtime.

## Frozen Surfaces

These proactive branches are frozen as regression evidence, not active development surfaces:

- `thought_probe`
- weak-generic rebind
- bare-continue repair
- proactive timing
- self-DM live gate

## Verification

Required commands:

```bash
python3 -m py_compile ego_desktop_lab/*.py
TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests -q
TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests/test_subjective_loop_consolidation_v1.py -q
git diff --check -- EgoCore OpenEmotion ego_desktop_lab docs
```

Current run result:

- `python3 -m py_compile ego_desktop_lab/*.py`: pass.
- `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests -q`: `189 passed`.
- `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests/test_subjective_loop_consolidation_v1.py -q`: `7 passed`.
- `git diff --check -- ego_desktop_lab docs/SUBJECTIVE_LOOP_V1_PRODUCT_CUT_REPORT.md docs/codex/tasks/subjective-loop-v1-product-cut`: pass.
- `git diff --check -- EgoCore OpenEmotion ego_desktop_lab docs`: blocked by pre-existing unrelated trailing whitespace in runtime artifacts/logs under `EgoCore/` and `OpenEmotion/`; this slice did not touch those files.

Focused parity coverage:

- `test_lab_and_mainline_decision_class_parity`
- `test_feedback_changes_next_reply_plan`
- `test_affective_grounding_before_next_step`
- `test_authority_boundaries_for_consolidation_contract`

## Authority Boundary

- EgoCore must not write self-model or appraisal state.
- OpenEmotion must not execute transport, desktop, or external actions.
- Shell and Telegram must not recalculate selected decisions.
- `ego_desktop_lab` must stay a harness / reference kernel, not a separate runtime authority.

## Claim Ceiling

This report supports only `replay-validated subjective-agent proxy`.

It does not prove consciousness, alive status, soul, live autonomy, runtime efficacy, real semantic intelligence, or production user value.
