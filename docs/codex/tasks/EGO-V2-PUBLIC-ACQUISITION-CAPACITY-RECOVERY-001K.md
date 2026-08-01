# EGO-V2-PUBLIC-ACQUISITION-CAPACITY-RECOVERY-001K

## Status and authority

- Task ID: `EGO-V2-PUBLIC-ACQUISITION-CAPACITY-RECOVERY-001K`
- Base HEAD: `7287a40e352fccf6f17683cef78a08c6ebab163a`
- Branch: `codex/ego-v2-public-acquisition-capacity-recovery-001k`
- Scope: dev-only offline capacity-recovery research campaign.
- Publication: local commits only; no push, tag, or remote anchor.
- Frozen predecessor `EGO-V2-HOMEOSTATIC-COMPOSITIONAL-TRANSFER-001J`
  source, packet, results, and artifacts are read-only evidence. They may be
  audited but must not be rerun or modified.

This card does not authorize M1-M3, a neural learner, product engine changes,
or consumption of the eight original 001J heldout assignments.

## Program goal

Determine why a legal public-history reference failed to exploit an existing
oracle-random deficit-AUC headroom, then test whether a reproducible,
non-leaking, non-overfit public acquisition reference can recover that
headroom. The objective is mechanism identification, not tuning one stored
result positive.

## Claim ceiling

At most, this campaign can establish public rule-acquisition capacity inside
the frozen successor benchmark packets. It cannot establish general transfer,
agency, subjectivity, consciousness, self-generated drives, or real-world
survival ability.

## Hard input boundary

A legal reference receives only:

- current public egocentric visual observation;
- current energy and safety;
- prior public actions and their observed action outcome/delta history;
- its own serialized public-history state and declared public RNG.

The reference must never receive world/seed/layout identity, token mapping,
private pose, object coordinates, cause labels, oracle action, split/packet
label, future information, evaluator verdict, or evaluator-only posterior.
Evaluator-only diagnostic arms may use private truth solely to localize a
failure and must be excluded from qualification claims.

## Frozen campaign budget

- At most three mechanism stages.
- At most four formal search candidates per stage.
- Each candidate changes one declared mechanism variable relative to its
  stage baseline.
- Search failures remain in the trial registry and result artifacts.
- Qualification is single-use after candidate source, parameters, packet
  assignment, thresholds, and source hashes are frozen.
- A failed qualification packet cannot be tuned or rerun.
- Replication uses a separately pre-frozen, previously unexecuted dev-only
  packet and is single-use.

## Packet layers

1. `search-dev`: repeatable diagnosis and candidate selection only.
2. `qualification`: one formal execution after candidate freeze.
3. `replication`: one formal execution after qualification, without retuning.
4. Original 001J heldout: untouched and outside this task.

All three 001K packets use new task-local seeds and opaque context IDs. Their
private assignment files and hashes are frozen before candidate
implementation. Private assignment fields are evaluator inputs, never policy
inputs.

## Stage hypotheses and cheapest discriminating tests

### S1 - public observability

Hypothesis: legal public history cannot identify token effect signs or useful
topology quickly enough.

Strongest rebuttal: the public observation shows anonymous tokens and an
egocentric local map, while observed interaction deltas directly identify
token consequences; poor performance may instead be a planner wiring defect.

Cheapest tests:

- reconstruct token/action effect-sign accuracy from public history;
- plot accuracy and cumulative acquisition cost by interaction step;
- compare no-history, update-frozen, feedback-shuffled, and full-history
  states without changing navigation.

### S2 - acquisition strategy or action budget

Hypothesis: effects are learnable, but unsafe/inefficient probing or the
96-action horizon prevents benefits after acquisition.

Strongest rebuttal: the 001J reference spent most actions turning, which may be
a planner target-retention defect rather than an exploration-budget problem.

Cheapest tests:

- keep the planner fixed and change only probe scheduling/risk constraint;
- compare prefix metrics at 48/96/192 actions;
- compare deterministic risk-constrained information gain and public Thompson
  sampling using the same public posterior.

### S3 - model/planner wiring

Hypothesis: posterior state updates, but target selection/path execution does
not consistently read or act on it.

Strongest rebuttal: even a correctly wired local navigator may fail if local
observations do not support stable localization or if acquisition is too
costly.

Cheapest tests:

- prove update -> ranked posterior -> selected target/action receipts;
- evaluator-only true-posterior substitution to separate learning from
  planning;
- posterior-value, target-retention, and planner-ranking ablations;
- verify that changing a learned token sign changes action ranking under a
  fixed public observation and organism state.

## Metrics

For every search candidate record:

- hypothesis, one mechanism change, preregistered prediction;
- random/oracle/public mean deficit-AUC loss;
- `public_reference_gain = random_loss - public_loss`;
- `recovery_fraction = public_gain / (random_loss - oracle_loss)`;
- per-world paired direction count;
- effect-sign acquisition curve and cumulative acquisition cost;
- failure explanation and next-stage authorization.

Lower deficit-AUC loss is better.

## Gates

Phase signal only:

- `public_reference_gain > 0`.

M1 authorization remains unchanged and requires all of:

- recovery fraction at least `0.50`;
- public better than paired random in at least `12/16` worlds;
- deterministic row recomputation and replay;
- no-update, feedback-shuffle, or posterior ablation materially damages the
  gain;
- leakage and tamper positive controls fail closed;
- a separately frozen replication packet reproduces positive gain with a
  majority positive paired directions.

If gain is positive but recovery is below `0.50`, verdict must be
`POSITIVE_SIGNAL_BUT_M1_NOT_AUTHORIZED`.

If the budget ends without reproducible positive gain, verdict must be
`PUBLIC_ACQUISITION_CAPACITY_STILL_INCONCLUSIVE`.

## Stop and successor rules

- Do not change public observation, action semantics, metabolism, or world
  grammar under this Task ID.
- If any such change is needed, stop and author a new benchmark successor.
- Do not tune after qualification output is visible.
- Do not run replication with a different candidate than qualification.
- Do not implement the neural candidate under this task.
