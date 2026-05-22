# Plan

## One Hypothesis

If the judge packet contains compact trace evidence and the harness cleans up unresolved approvals between independent cases, GPT-5.5 can separate true mechanism evidence from conversational warmth and case contamination.

## Change Surface

- `scripts/run_ego_experience_trial.py`
- `scripts/tests/test_run_ego_experience_trial.py`
- `scripts/ego_functional_subject_judge_schema.json`
- `Tasks/TASK_BOARD.yaml`
- `.codex/project_contract.yaml`

## Steps

1. Add a trace evidence extractor for Functional Subject trial rows.
2. Add case-boundary pending approval rejection for scripted independent cases.
3. Add cleanup trace and in-session cleanup memory so later cases do not see stale pending commitments.
4. Make the Functional Subject judge schema strict-output compatible.
5. Add deterministic tests.
6. Rerun real-provider smoke and GPT-5.5 judge.

## Verification

- `python3 -m py_compile scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py scripts/ego_functional_subject_judge_schema.json`
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py`
- `OPENROUTER_API_KEY=<redacted> python3 scripts/run_ego_experience_trial.py --functional-subject-trial --out /tmp/ego_functional_subject_real_provider_smoke_v2`
- `codex exec --ephemeral --sandbox read-only --model gpt-5.5 --output-schema scripts/ego_functional_subject_judge_schema.json - < /tmp/ego_functional_subject_real_provider_smoke_v2/judge_prompt.txt`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full`
