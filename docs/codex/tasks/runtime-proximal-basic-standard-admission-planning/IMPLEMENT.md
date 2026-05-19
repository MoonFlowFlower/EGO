# Runtime-Proximal Basic-Standard Admission Planning - IMPLEMENT

## Scope

This task is planning-only.

Allowed changes:

- planning docs
- repo state / progress wording
- evidence ledger
- research campaign checkpoint / ledger / scorecard

Not allowed:

- new runtime code
- new public API
- new authority path
- new scorer ontology
- runner implementation

## Deliverables

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `EXPLORE.md`
- `BASIC_STANDARD_ADMISSION_FREEZE.md`

## Validation floor

- syntax-free docs update only
- `python3 scripts/codex/generate_program_state_views.py`
- `python3 scripts/codex/check_program_state_integrity.py --skip-diff-check`
- `git diff --check -- <scoped files>`
