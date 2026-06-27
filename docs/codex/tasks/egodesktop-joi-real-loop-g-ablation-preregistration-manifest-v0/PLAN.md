# EgoDesktop Joi Real-Loop G-ABLATION Preregistration Manifest v0 Plan

1. Recover current repo state, 009/010 docs, and live artifact hashes.
2. Freeze `PROMPT_PACKS.json` with 160 calibration prompts and 160 heldout prompts.
3. Freeze `PREREGISTRATION_MANIFEST.json` with:
   - source artifact hashes and current input boundary;
   - split protocol;
   - D-field whitelist and metric definition;
   - equivalence/power design;
   - same-access baseline battery with full-public-history steelman;
   - mechanism-presence and leakage controls;
   - outcome-blind verdict matrix;
   - explicit no-authority flags.
4. Write SHA256 sidecar files for the manifest and prompt packs.
5. Add task status, review stub, mutation scope, and task-board entry.
6. Regenerate route-convergence views.
7. Run local checks:
   - JSON parse for manifest and prompt packs;
   - SHA sidecar verification;
   - YAML parse for `Tasks/TASK_BOARD.yaml` and 011 `MUTATION_SCOPE.yaml`;
   - `git diff --check`;
   - `python scripts\codex\verify_route_convergence.py`;
   - `python scripts\codex\verify_repo.py --mode fast`;
   - scoped closeout check.
8. Send a compact source-limited packet to desktop Claude asking for exactly:
   - `NO_BLOCKING_FINDINGS`, with next minimal action; or
   - `BLOCKING_FINDINGS`, with numbered blockers, required repairs, and next minimal action.
9. If Claude blocks, repair only the manifest/card surface and loop.
10. If Claude returns no blocking findings, commit locally only.

## Non-Goals

- No `CREATURE_ON` capture.
- No same-access run.
- No scoring, comparison, verdict, route advancement, program-state update, evidence-ledger update, push, tag, or
  remote anchor.
