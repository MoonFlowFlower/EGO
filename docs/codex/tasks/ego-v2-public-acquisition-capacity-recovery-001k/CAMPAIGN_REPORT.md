# 001K dev-only capacity-recovery campaign report

## Bounded verdict

`POSITIVE_SIGNAL_BUT_M1_NOT_AUTHORIZED`

The campaign obtained reproducible positive acquisition headroom from legal
public inputs on two independently precommitted dev-only packets. The frozen
qualification packet crossed the unchanged 50% recovery threshold, but the
unchanged replication packet recovered only 40.95%. Therefore the evidence is
strong enough to report a reproducible positive benchmark signal, but not
strong enough to authorize M1.

No original 001J formal trajectory was rerun. Its eight heldout assignments
were not consumed. No product runtime source, observation, action semantics,
world grammar, M1-M3 path, or neural learner was changed or executed.

## Campaign budget and discipline

- Three mechanism stages used; maximum three.
- Four search candidates per stage; maximum four.
- Every search candidate and failed prediction is retained in
  `experiment_log.jsonl`, `search_results.json`, `search_rows.jsonl`, and
  `failure_manifest.json`.
- Search-dev was the only repeatable layer.
- Qualification was executed once after source/config/threshold freeze.
- Replication was executed once with the exact qualification candidate.
- Three action RNG seeds were used for each formal packet.

## Call-chain audit

Before adding a candidate algorithm, the campaign proved:

1. all frozen 001J task/source/artifact hashes matched;
2. source order was plan -> transition -> actual outcome -> metabolism ->
   posterior update;
3. a synthetic legal public update changed posterior state, the planner read
   the resulting state hash, and final action selection changed;
4. stored 001J public rows were 91.47% turns, with only 64 successful
   interactions and no trajectory identifying all five tokens.

Thus the posterior was not simply disconnected. The remaining question was
whether it was used through a competent acquisition/navigation policy.

## Mechanism adjudication

### 1. Public observability

**Hypothesis:** public history lacks enough information to identify anonymous
token effects and topology.

**Strongest rebuttal tested:** replace the learned posterior with the correct
evaluator-only posterior while keeping legacy planning unchanged.

**Evidence:**

- Full public history reached mean final effect-sign accuracy `0.5875`, but
  gain was `-0.04666`.
- No-update and feedback-shuffle remained negative and were not materially
  worse than full history under the legacy planner.
- A correct evaluator-only posterior reached accuracy `1.0`, yet recovered only
  `1.51%` headroom, with `6/16` positive directions and `95.70%` turns.
- After the geometry repair, legal public updates reached accuracy `1.0` on
  search-dev and qualification and `0.9625` on replication.

**Judgment:** insufficient public observability is not the primary explanation
inside this benchmark. Public interaction outcomes contain enough information
to identify deterministic token-effect signs. This does not establish that
arbitrary worlds are publicly identifiable.

### 2. Acquisition strategy and action budget

**Hypothesis:** acquisition is possible, but probing is inefficient or 96
actions are insufficient.

**Strongest rebuttal tested:** hold geometry and posterior update fixed, compare
48/96/192 actions, then change only the unknown-token information value at 96.

**Evidence:**

- Recovery rose monotonically from `25.11%` at 48 actions, to `31.09%` at 96,
  to `43.46%` at 192.
- More time helped but did not cross 50%, so budget alone was insufficient.
- Risk-constrained information value at 96 actions improved search recovery to
  `45.58%`, with `15/16` positive directions.
- This exact candidate later crossed 50% on qualification but not replication.

**Judgment:** action budget and probe scheduling are secondary real
contributors. They do not fully explain the packet-to-packet variation.

### 3. Reference model/planner wiring

**Hypothesis:** posterior updates are real but the planner/navigation wiring
does not convert them into useful action sequences.

**Strongest rebuttal tested:** change only front-diagonal steering geometry,
then separately add target retention, alternate deficit ranking, and a
posterior-ranking ablation.

**Evidence:**

- Geometry-only repair reduced turns from `92.90%` to `48.37%`, increased mean
  successful interactions from `4.0` to `20.75`, learned all five effects, and
  improved recovery from `-8.86%` to `31.09%` with `14/16` positive worlds.
- Target retention and alternate deficit ranking were weaker than the
  geometry-only candidate.
- Posterior-ranking ablation fell to `11.28%` recovery and `7/16` positive
  directions.

**Judgment:** the dominant diagnosed defect was planner geometry: the legacy
planner turned whenever horizontal offset was nonzero, including front-
diagonal targets, creating turn oscillation. Posterior acquisition mattered
only after this wiring defect was removed.

## Formal packets

### Qualification — single use

- Oracle loss: `0.189427`
- Public loss: `0.431255`
- Random loss: `0.718425`
- Public gain: `0.287170`
- Recovery: `54.29%`
- Positive trajectories: `47/48`
- Positive world aggregates: `16/16`
- Final effect-sign accuracy: `1.0`
- All three formal ablations materially damaged gain.
- Candidate replay exact; all candidate input receipts clean.
- Independent recomputation: 27,648 rows, no findings.
- Verdict: `QUALIFICATION_CAPACITY_ESTABLISHED_PENDING_REPLICATION`

### Replication — single use, unchanged candidate

- Oracle loss: `0.143678`
- Public loss: `0.492930`
- Random loss: `0.735164`
- Public gain: `0.242234`
- Recovery: `40.95%`
- Positive trajectories: `44/48`
- Positive world aggregates: `15/16`
- Final effect-sign accuracy: `0.9625`
- All three formal ablations materially damaged gain.
- Candidate replay exact; all candidate input receipts clean.
- Independent recomputation: 27,648 rows, no findings.
- Verdict: `POSITIVE_SIGNAL_BUT_M1_NOT_AUTHORIZED`

## Integrity controls

- Combined independent recomputation covered 55,296 formal rows.
- Stored row-value tamper was rejected.
- Stored aggregate tamper was rejected.
- Candidate receipt private-field injection was rejected.
- Packet-assignment byte tamper was rejected.
- Seed, world/layout identity, mapping, private pose, cause, oracle action,
  split, and future-field positive controls were rejected.
- Candidate source and packet commitments remained equal to their pre-run
  freeze.

## Regression verification

- 001K producer/verifier tests: `10 passed`.
- Frozen 001A producer/verifier tests under NumPy 2.2.6: `13 passed`.
- V2 microworld tests: `12 passed`.
- The broader V0 playground suite retained two pre-existing version-assertion
  failures: the test expects trace schema `v14` and code-path schema `v10`,
  while the base HEAD already implements `v15` and `v11`. The 001K diff changes
  neither `labs/ego_life_playground_v0/**` nor that test file; these failures
  are reported rather than silently repaired outside scope.

## What the campaign establishes

Within this bounded microworld grammar, a legal public-history reference can:

- acquire anonymous action-conditioned effect signs;
- use those learned effects to outperform a paired random policy;
- lose most of that advantage under no-update, shuffled-feedback, or posterior
  ablation;
- reproduce positive headroom on a separately frozen dev-only packet.

## What it does not establish

It does not establish M1 authorization because the replication recovery
fraction was below 50%. It also does not establish generic compositional
transfer, arbitrary-world identifiability, a self-generated goal, agency,
subjectivity, free will, consciousness, electronic life, or real-world
survival ability.

## Next frontier

Stop this Task ID. A later benchmark successor may study why recovery varies
from 54.29% to 40.95% across precommitted packets, using new search-dev data.
It must not retune or rerun these qualification/replication packets. Any change
to observation, action semantics, or world grammar requires an explicit new
benchmark successor.
