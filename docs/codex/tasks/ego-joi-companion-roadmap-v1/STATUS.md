# Status

Current milestone: `roadmap_bootstrap_and_scripted_smoke_contract`

## Decisions

- Use Joi as a mechanism reference, not a clone or prompt source.
- GPT-5.5 judge can review scripted companion smoke, but cannot raise claim ceiling or override hard stops.
- Live2D/desktop embodiment is part of the roadmap, but starts as architecture-only.

## Current Observations

- GitHub issues `#74` through `#82` were created for Epic 9 and first child tasks.
- GitHub Project readback hit GraphQL API rate limit during verification; status verification remains pending.
- Local quote-safe matrix and 12-turn Chinese companion smoke pack are in place.
- `scripts/run_ego_experience_trial.py --companion-smoke` can emit a companion smoke report and GPT-5.5 judge packet.

## Verification

- `python3 -m py_compile scripts/run_ego_experience_trial.py scripts/validate_experience_eval_contract.py` -> pass.
- `python3 scripts/validate_experience_eval_contract.py` -> pass, including `joi_companion.turn_count = 12`.
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_experience_eval_contract.py scripts/tests/test_run_ego_experience_trial.py` -> pass.
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_codex_project_autopilot.py` -> pass.
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests` -> pass (`170 passed`).
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass (`217 passed` plus scoped diff check).
- `python3 scripts/run_ego_experience_trial.py --companion-smoke --turn-limit 3 --out /tmp/ego_companion_smoke_test` -> pass with `scripted_companion_provider_unavailable` because this shell has no live provider.

## Next Step

After local verification and push, rerun Project verification when GitHub GraphQL quota recovers.
