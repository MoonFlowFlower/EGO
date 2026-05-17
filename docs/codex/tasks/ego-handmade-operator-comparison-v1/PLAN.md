# Ego Handmade Operator Comparison v1 - PLAN

## Implementation Steps

1. Add a candidate-local comparison harness under `Ego_handmade`.
2. Encode five operator scenarios: opinion chat, file creation request, Python debugging, long-task breakdown, and tool rejection recovery.
3. Reuse the existing 20-case Dark Souls paraphrase suite.
4. Record old-system baselines as reference entrypoints only unless a low-cost deterministic comparable runner is available.
5. Write JSON and Markdown comparison reports to ignored `Ego_handmade/artifacts/comparison/`.
6. Add targeted tests for scenario coverage, gate behavior, report shape, baseline honesty, and no runtime route/template markers.
7. Update `STATUS.md` only after verification.

## Rollback

Remove the comparison harness, comparison tests, generated ignored comparison
artifacts, and this task directory. No formal authority or evidence-ledger
rollback is needed because this task does not touch those paths.
