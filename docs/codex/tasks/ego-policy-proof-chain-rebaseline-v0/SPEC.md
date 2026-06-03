# EGO-FS-097: Policy Proof-Chain Rebaseline from Tracked Inputs v0

## Summary

Rebaseline the policy default-enablement proof source chain so it can reproduce
from tracked sample packs in the current worktree. The issue exposed by
EGO-FS-096 is not default-enablement readiness; it is that the proof runner's
source target depended on a brittle first-10-case slice and no longer found the
candidate-eligible feedback target.

This task may repair the proof-chain runner. It must not enable default policy
behavior.

## Structure Risk Self-Check

- This solves the real blocker from EGO-FS-096: proof evidence drift and
  non-reproducible source target selection.
- It avoids a second truth source by using tracked Functional Subject sample
  packs instead of stale `/tmp` artifacts.
- It preserves gate order: proof-chain reproducibility first, reviewer/human
  evidence later, default-on behavior last.
- Strongest counterexample: the proof runner passes only because the target is
  hand-injected rather than found in tracked replay.
- Acceptance proves proof-chain reproducibility, not default enablement.

## Change Surface

Allowed:

- adjust proof-chain runner case selection;
- expose optional CLI paths for human sanity / real-provider observation JSON;
- add focused tests that prevent returning to a brittle first-10-case target.

Not allowed:

- default-enable policy patch behavior;
- write memory;
- execute tools or approvals;
- train a model;
- modify `docs/PROGRAM_STATE_UNIFIED.yaml`;
- write `artifacts/evidence_ledger/**`;
- change legacy runtime ownership.

## Acceptance Gate

- Candidate-eligible feedback pack finds at least one target from tracked sample
  inputs by default.
- Feedback runtime ablation proof passes with target improvement and rollback
  disabled arm clean.
- Policy opt-in proof arm passes and keeps default behavior disabled.
- Policy reviewer packet passes and still holds default enablement.
- Default-enablement proof can consume an explicit latest #94 observation path;
  with no current human sanity JSON it remains partial for the human gate only.
- No tools, pending approvals, memory writes, training, program-state writes, or
  evidence-ledger writes occur.

## Rollback

Revert the runner/test changes, remove this task directory, remove `EGO-FS-097`
from `Tasks/TASK_BOARD.yaml`, and delete the Loop 126 pursue-goal ledger/doc
entries.

## Claim Ceiling

`Policy proof-chain rebaseline local/scripted candidate pass`.

This does not claim default enablement, runtime efficacy, stable user benefit,
live autonomy, durable memory efficacy, real subjective experience,
independent personhood, or consciousness.
