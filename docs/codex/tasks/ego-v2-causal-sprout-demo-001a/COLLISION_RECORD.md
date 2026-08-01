# Collision record — EGO-V2-CAUSAL-SPROUT-DEMO-001A

## Workspace collision readback

- Repository root: `D:/Project/AIProject/MyProject/Ego`.
- Pre-task branch: `codex/ego-v2-bayesian-active-identification-001h`.
- Base HEAD: `144782376baf74c4e01519b9cf019d949e3d7f2c`.
- Pre-task status: clean; index empty; worktree diff empty.
- Existing linked worktrees: only this checkout.
- Target branch did not previously exist and was created as
  `codex/ego-v2-causal-sprout-demo-001a`.
- Overlapping edits: none observed.
- Collision disposition: same checkout is safe; no reset, clean, stash,
  rebase, overwrite, or second worktree required.

## Mechanism collision readback

### Candidate A — token/outcome lookup

- **What it measures:** repeat-surface association under equal public access.
- **Strongest cheap explanation:** cached feature/action outcomes.
- **Smallest falsifier for the candidate claim:** candidate does not beat this
  lookup after correlation reversal and unseen composition.
- **Disposition:** mandatory invalidating control, not the selected learner.

### Candidate B — authored causal graph / if-else selector

- **What it measures:** benchmark solvability with privileged mechanism truth.
- **Strongest objection:** the purported mechanism is written by the author.
- **Smallest leakage test:** inject forbidden hidden-channel/context/oracle
  fields and require the public-input scanner to reject them; scan learner
  source for feature/token/context-specific action branches.
- **Disposition:** evaluator-only reference; its outputs are never learner
  inputs, targets beyond actual observed delta, policy guidance, or thresholds.

### Candidate C — recurrent neural learner

- **What it could measure:** history- and update-dependent predictive transfer
  under paired interventions.
- **Strongest cheap match:** no-update RNN, feed-forward learner, lookup,
  nearest neighbour, and surface predictor on identical public rows.
- **Smallest falsifier:** any equal-access invalidating control matches its
  frozen heldout interventional loss/effect profile, or reset history does not
  damage the history-required subset.
- **Expected failure modes:** surface memorization, schedule/context-order
  leakage, recurrent state unused, optimizer not connected, or artifact-only
  replay that reads stored decisions.
- **Disposition:** selected only as a falsifiable learner, with no causal claim
  unless every preregistered gate passes.

## Architecture collision

Three implementation routes were compared:

1. **Standalone demo engine/store:** fastest, but creates a second runtime and
   weakens replay-boundary evidence. Rejected.
2. **Rewrite the ordinary microworld reducer/schema:** strongest physical
   integration but needlessly risks protected V2 behavior and old evidence.
   Rejected.
3. **Inject a task-local deterministic runtime adapter into the existing
   `PlaygroundController` and `SQLiteEventStore`:** live dispatch and recovery
   call the same reducer, while ordinary runtime defaults remain unchanged.
   Selected.

The selected route must fail closed if controller and store receive different
runtime adapters. The renderer is trace-only and has no transition logic.

## Stop conditions

Stop or downgrade without threshold tuning if any of these occurs:

- overlapping workspace mutation appears;
- hidden evaluator fields reach learner/baseline inputs;
- heldout is revealed before freeze or rerun after reveal;
- stored action/prediction/outcome becomes a replay input;
- lookup/no-update/surface controls match candidate;
- update or recurrent-history ablations do not damage the claimed effect;
- formal science seed namespace is consumed;
- exact required artifact or tamper check is missing.
