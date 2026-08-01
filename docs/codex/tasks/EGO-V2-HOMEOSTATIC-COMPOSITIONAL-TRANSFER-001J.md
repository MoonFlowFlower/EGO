# EGO-V2-HOMEOSTATIC-COMPOSITIONAL-TRANSFER-001J

## Bounded task contract

- **Task ID:** `EGO-V2-HOMEOSTATIC-COMPOSITIONAL-TRANSFER-001J`.
- **Task type:** gated local V2 product/mechanism successor.  M0 is a
  candidate-free capacity certificate; M1--M3 are authorized only if M0
  passes its frozen dev-only gate.
- **Repository:** `D:\Project\AIProject\MyProject\Ego`.
- **Branch:** `codex/ego-v2-homeostatic-compositional-transfer-001j`.
- **Base HEAD:** `55b1e8622cd24c425b5fe6f334bc2bb3a5bb0016`.
- **Runtime authority:** the existing explicit/default-off V2 chain only:
  `PlaygroundController.dispatch -> engine.compute_step -> world transition ->
  metabolism -> terminal check -> SQLite append/recover/recompute`.
- **Publication:** local commits only; no push, tag, or remote anchor.
- **Protected evidence:** all prior 001A and 001C--001I cards, artifacts,
  verdicts, heldout packets, and seeds remain immutable.
- **Claim ceiling:** bounded local acquisition, homeostatic action wiring, and
  same-grammar compositional-transfer evidence only.  No agency,
  consciousness, subjectivity, autonomous goal formation, general learning,
  real-world survival, or electronic-life claim.

## Real target and non-goals

The fixed inherited drive is to reduce deficits in the existing `energy` and
`safety` organism variables.  The mapping from anonymous public observations
and actions to organism consequences must be learned from public interaction.
Slow learned parameters may transfer between worlds; world-local recurrent
belief must reset on a world change.  The action selector must consume the
learned consequences and current deficits, rather than a token/cause/world
lookup or a low-energy if/else rule.

This task does not optimize throughput, revive the revealed 001A heldout,
replace the controller/store, add curiosity as an independent drive, or change
network/LLM/background/default-enable policy.

## M0 frozen capacity certificate

### Complete factor grammar

The benchmark contains exactly 24 factor combinations:

```text
3 canonical layouts x 4 anonymous token/effect mapping families
                    x 2 initial homeostatic profiles
```

- layouts use the three existing canonical `microworld.LAYOUTS` entries;
- mapping families are the first four distinct complete token mappings found
  by lexical integer search in task-local world IDs `20000..25999`;
- profiles are `energy_low` (`energy=0.28,safety=0.62`) and `safety_low`
  (`energy=0.62,safety=0.28`), with existing connection/stimulation defaults;
- a combination is held out iff
  `(layout_index + mapping_index + profile_index) % 3 == 0`, yielding exactly
  eight heldout combinations and sixteen dev combinations;
- every primitive factor level must occur in both partitions;
- only the dev partition may be executed during M0.

Every arm receives the same public observation, organism state, legal action
set, action budget, and observed transition receipts.  World ID, layout ID,
private pose, cause, token mapping, future observation, oracle action, split,
and verdict are forbidden learner/reference inputs.  Evaluator-only oracle
code may inspect private state but may never feed its values or actions into a
public arm.

### Capacity arms

1. `PRIVATE_ORACLE_NAVIGATOR`: evaluator-only shortest legal route to the
   currently most deficit-reducing resource/shelter interaction.
2. `PUBLIC_FACTOR_BAYES`: public-observation navigator plus online anonymous
   token/action outcome posterior; it starts without token meaning and updates
   only from its own observed actions and organism deltas.
3. `UNIFORM_RANDOM`: deterministic seeded uniform legal action control.

Each dev combination is run for 96 evaluator-forced legal action transitions.
M0 is an offline admission harness, not a product action path: every transition
must invoke the unchanged `microworld.transition_world`,
`engine.compute_actual_delta`, and `engine.compute_metabolism_ledger` callables
and independently check their receipts.  It may not copy their world or
metabolism rules, mutate engine source, create a controller/store, or claim
runtime integration.  Natural death/respawn uses the unchanged world reset
callable and does not reset the public reference's learned token posterior.
Primary loss is mean per-step
`max(0,0.72-energy)+max(0,0.72-safety)` plus `1.0` for an uncensored death.

M0 passes only if all of the following are true without threshold changes:

- all 16 dev combinations and three arms execute through the unchanged
  transition/outcome/metabolism callables with invocation receipts;
- mean random-minus-oracle deficit loss is at least `0.10`;
- `PUBLIC_FACTOR_BAYES` recovers at least `0.50` of the positive
  random-to-oracle headroom;
- the reference beats random in at least 12 of 16 dev combinations;
- input leakage, same-public-input receipts, replay, and independent aggregate
  recomputation pass.

Any M0 failure emits `BENCHMARK_CAPACITY_NOT_ESTABLISHED`, writes the negative
artifact/failure manifest, and stops before `homeostatic_transfer.py`, engine
integration, source freeze, or heldout-ID commitment.

## M1 two-timescale candidate, conditional on M0 PASS

The sole candidate is a NumPy recurrent action-outcome model with:

- serialized slow weights/optimizer/RNG that persist across deaths and worlds;
- serialized fast world belief that persists across lives in one world and is
  reset only by `reset_for_world`;
- death-local eligibility/credit trace cleared by `reset_for_respawn`;
- public inputs limited to visual observation, energy, safety, prior action,
  and actual prior energy/safety deltas;
- per-action predicted energy delta, safety delta, terminal risk, and
  uncertainty;
- a fixed homeostatic planner that minimizes predicted deficit and terminal
  risk; no independently learned reward or policy-authority head.

The existing engine gains a mutually exclusive, default-off
`predictive_control_mode=homeostatic_transfer`.  In that mode Expected SARSA
must be `off` and cannot update or select actions.  Live and replay execution
invoke the same functions and serialize complete candidate state.

## M2 dev gate and M3 one-shot heldout

Equal-access controls are scratch candidate, no-update, slow reset, fast reset
each step, shuffled feedback, surface lookup, inherited SARSA, inherited
factored predictor, public Bayes, oracle, and random.  M1 may enter freeze only
if the neural candidate recovers at least half the public-reference transfer
headroom on dev.

After source/config/test/threshold/baseline freeze, eight heldout combinations
are assigned opaque unconsumed world IDs and run once under three frozen
action-RNG seeds.  Maximum positive verdict requires:

- effect-sign accuracy at least `0.80`;
- transfer gain at least `0.05` of scratch-to-oracle headroom and positive in
  at least 18 of 24 paired trajectories;
- negative-transfer late loss no worse than scratch by more than `0.05` of
  oracle-to-random headroom;
- update/slow-reset destroys at least half the observed transfer gain;
- fast reset damages at least 75 percent of history-required trajectories;
- paired energy/safety drive interventions change every non-tied action rank
  in the predicted deficit-reducing direction, while drive-off preserves
  predictions and removes action sensitivity;
- fresh replay, row recomputation, artifact integrity, leakage, trace/weight/
  world-assignment tamper controls all pass.

No failed gate may be repaired by rerunning or retuning the revealed packet.

## TDD, evidence, and expected mutation surface

Order is:

```text
readback -> collision/scope/card -> capacity tests RED -> M0 producer GREEN
-> dev M0 run -> STOP or candidate tests RED -> M1/M2 implementation
-> dev gate -> STOP or freeze -> one heldout run -> replay/recompute/review
```

Evidence root is
`artifacts/EGO-V2-HOMEOSTATIC-COMPOSITIONAL-TRANSFER-001J/`.  M0 always writes
`capacity_result.json`, `capacity_rows.jsonl`, `capacity_replay_report.json`,
`leakage_report.json`, `artifact_manifest.json`, and, on failure,
`failure_manifest.json`.  M1--M3 add the transfer, ablation, drive,
intervention, replay, recomputation, trace, learner-state, freeze, HTML, result,
and claim-ceiling artifacts named in the operator plan.

The exact allowed paths are frozen in the sibling `MUTATION_SCOPE.yaml`.

## Stop and rollback

- Stop on workspace collision, authority drift, old-artifact drift, missing
  NumPy `2.2.6`, M0 failure, leakage, replay mismatch, heldout pre-reveal, or
  any equal-access/reference contradiction.
- Rollback removes only uncommitted 001J paths or returns to the last local
  001J phase commit.  Never reset, rewrite, or regenerate predecessor evidence.
