# Status

## Current Milestone

`EGO-FS-011` local implementation and verification.

## Decisions

- The harness now rejects pending approvals at case boundaries for independent scripted samples.
- The judge packet includes compact trace evidence instead of only trace file paths.
- #94 remains blocked because GPT-5.5 still returned `partial`; this task only fixes evidence quality.

## Evidence

- `python3 -m py_compile scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py scripts/ego_functional_subject_judge_schema.json` passed.
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py` passed with 14 tests.
- Real-provider smoke v2 produced 20 non-empty replies with OpenRouter:
  - `/tmp/ego_functional_subject_real_provider_smoke_v2/functional_subject_trial_report.json`
  - `/tmp/ego_functional_subject_real_provider_smoke_v2/functional_subject_trial_report.md`
- GPT-5.5 judge ran successfully and returned `partial`.
- Judge traceability score improved, but remaining blockers include memory-save wording and policy replay proof.

## Risks

- `/tmp` evidence is local operational evidence, not repo evidence ledger.
- The judge verdict remains partial, so Functional Subject real-provider smoke is not accepted.

## Next Step

Proceed to `EGO-FS-012`: memory-save gate wording repair.
