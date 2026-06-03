# Plan

## Milestone 1 - Environment Preflight

- Confirm whether `http://localhost:1234/v1/models` is reachable from the
  current execution shell.
- If unreachable, record `backend_unavailable` and stop before model comparison.
- If reachable, capture loaded model ids.

## Milestone 2 - Candidate Matrix

Compare at least two routes:

1. Current Cydonia local route with fast settings.
2. A second available local model, lower quant, smaller model, or alternate
   OpenAI-compatible backend.

If a second route is not available, record why and produce an explicit proposal
for model/backend setup.

## Milestone 3 - Real Runtime Smoke

Run each candidate through #80 adult-fiction smoke using the real
`run_ego_experience_trial.py` path with a private scenario file when available.

## Milestone 4 - Selection

Select one candidate for #80 strict 3/3, or declare the next blocker as
`model_capacity_blocker` / `backend_unavailable`.

## Decision Log

- 2026-05-27: Created because #80 strict 3/3 failed on local Cydonia capacity
  and the pursue-goal loop should not continue prompt patching as the main path.
