# Status

## Current Milestone

Accepted locally as review-required lifestyle seed evidence.

## Result

EGO-FS-109 repaired two post-EGO-FS-108 real-entry gaps:

- hidden thought/user-input-meta leakage is detected and rewritten before it is
  admitted to user-visible output;
- direct pressure to "fully follow me" routes to a bounded non-obedience native
  gate.

The repaired real-entry seed was appended to the active EGO-FS-100 lifestyle
trial as the third review-required session. The active review still returns
`partial`, which is expected: the session dimensions remain `unknown` until a
human reviewer assigns verdicts.

## Evidence

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py`
  -> pass
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py -k 'bounded_non_obedience_gate or thought_tag or self_orientation_summary'`
  -> `4 passed, 268 deselected`
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_functional_subject_lifestyle_trial.py`
  -> `13 passed`
- `env -u OPENROUTER_API_KEY TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests`
  -> `393 passed`
- `git diff --check -- EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py scripts/functional_subject_lifestyle_trial.py Tasks/TASK_BOARD.yaml docs/codex/tasks/ego-functional-subject-post-repair-lifestyle-session-v0 docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0 docs/codex/tasks/ego-pursue-functional-subject-goal-v1 artifacts/task_board`
  -> pass
- `/tmp/ego_fs109_lifestyle_post_repair_session_v0/combined_transcript.txt`
  -> pre-repair real-entry seed exposed hidden thought/user-input-meta leakage
- `/tmp/ego_fs109_lifestyle_post_repair_session_v1/combined_transcript.txt`
  -> leak repaired, but direct strategy pressure still regressed to a waiting
  line
- `/tmp/ego_fs109_lifestyle_post_repair_session_v2/combined_transcript.txt`
  -> post-repair seed shows bounded non-obedience and self-orientation summary
- `/tmp/ego_fs109_lifestyle_post_repair_session_v2/agent_trace.jsonl`
  -> includes `native_bounded_non_obedience_choice_gate`,
  `native_self_orientation_summary_gate`, and
  `native_session_only_memory_boundary_gate`
- `/tmp/ego_fs109_lifestyle_post_repair_session_v2/draft/functional_subject_lifestyle_trial_session.json`
  -> `requires_human_review=true`
- `/tmp/ego_fs109_lifestyle_post_repair_session_v2/active_review/functional_subject_lifestyle_trial_review.json`
  -> `functional_subject_lifestyle_trial_review_partial`,
  `session_count=3`, `dimension_evidence_missing`, `session_review_required`
- GitHub mirror:
  [#124](https://github.com/pen364692088/EGO/issues/124) -> issue `CLOSED`,
  Project status `Done`

## Decision

Accept EGO-FS-109 as a local/real-entry candidate repair and review-required
seed capture. This is stronger than harness-only proof because the failures and
repairs were observed through the real EgoOperator CLI path. It is not a #94
closeout and does not make the lifestyle trial pass.

## Remaining Risk

The v2 seed still contains askback tendency in open-ended provider turns. That
is recorded as quality evidence for review rather than hidden. The next route
is human review or reviewer-authored decision files for the three active
sessions, not another helper micro-task by default.

## Next

Review the three active lifestyle sessions with the current packet, create
reviewer-authored decision JSON files where supported, apply them, export/review
again, and continue collecting reviewed sessions before #94 closeout or default
enablement.

## Rollback

Revert the internal leak pattern expansion, rewrite instruction, bounded
non-obedience pattern expansion, regression tests, EGO-FS-109 task record, the
appended `codex-seed-day1-post-repair-self-orientation-v3` session, and Loop 138
pursue-goal records.
