# EGO-R0-KERNEL-STATE-SUBSTRATE-001A — Kernel State Substrate (executable)

Status: EXECUTABLE / DEFAULT-OFF / NOT_RUNTIME_CONNECTED.
Parent: `ego-mechanism-rewrite-decision-001a` (R0 row; contracts may be
narrowed here, never widened). Created 2026-07-06.

## Objective

Build the engineering substrate every later component runs on: a kernel
state container with canonical serialization and hashing, a deterministic
tick loop, a versioned trace schema, a fresh-process replay harness, a
state-causality smoke test, and an LLM-swap invariance harness skeleton —
validated against a purpose-built probe substate. No mechanism content, no
runtime wiring, no EgoDesktop/src or EgoOperator modification.

## Scope / layout (Python side; JS adapter belongs to the future R3-adoption card)

```text
scripts/ego_kernel/__init__.py
scripts/ego_kernel/state.py     # KernelState: named substates, canonical
                                # sorted-keys JSON serialization, sha256
                                # state_hash, schema_version, seed registry
                                # (every RNG seed lives IN the state)
scripts/ego_kernel/tick.py      # (state, observation) -> (action, state');
                                # per-substate registered update rules,
                                # deterministic given registered seeds
scripts/ego_kernel/trace.py     # kernel_trace_v0 jsonl writer/reader
scripts/ego_kernel/replay.py    # replay from serialized state + input log;
                                # in-process AND fresh-subprocess modes
scripts/ego_kernel/probe_substate.py   # validation payload (below)
scripts/run_ego_kernel_substrate_validation.py   # runner -> artifacts
tests/test_ego_kernel_substrate.py
docs/codex/tasks/ego-r0-kernel-state-substrate-001a/MUTATION_SCOPE.yaml
artifacts/ego_r0_kernel_state_substrate_001a/
```

Keep each `.py` < ~250 lines (split rather than grow). No network, no API
keys, no real LLM calls anywhere in R0.

## Trace schema `kernel_trace_v0` (per tick; nullable where probe unused)

`task_id, run_id, episode_id, step_id, state_before_hash, observation,
prediction (nullable), action, feedback (nullable), prediction_error
(nullable), state_after_hash, component_attribution, seed_context`.

Field-naming rule: where a field semantically matches the existing
`egodesktop_joi_real_loop_g_ablation` backend-trace vocabulary, reuse that
name; divergences are listed in a `SCHEMA_NOTES.md` beside the card. One
lane, one vocabulary — no second schema by accident.

## Probe substate (validation payload — exercises every contract feature)

Three registered substates:
1. `pref_ema`: drifting preference over K=4 options, EMA-updated from
   observation; the probe ACTION = argmax(pref) → state-implied behavioral
   direction is well-defined by construction.
2. `counter`: deterministic tick counter (trivial regression anchor).
3. `noise_user`: consumes a REGISTERED rng stream each tick (proves seed
   discipline; its output mixes into action tie-breaking).
Each has a live ablation switch: `live | frozen | zeroed` (frozen = no
update; zeroed = substate reset each tick).

## Predeclared run plan (frozen at card landing; no post-hoc changes)

- Episodes: 3 per seed; seeds: {11, 23}; ticks per episode: 300.
- Input logs: synthetic observation streams generated once from a seeded
  generator and SAVED as fixtures (the same fixtures drive replay and
  causality runs).
- Checkpoints: serialize full state at ticks {0, 100, 200, 300}.

## Acceptance gates (all predeclared; tolerance changes = card violation)

- **G-R0-REPLAY** (decisive): for every episode: (a) full-run action
  sequence + all state hashes reproduced from tick-0 state + input log in a
  fresh subprocess, x2 runs, mismatches = 0; (b) mid-episode resume: restore
  checkpoint tick-100 state, replay ticks 101-300, must equal the
  uninterrupted run exactly. Zero tolerance.
- **G-R0-CAUSALITY**: same input log, two initial states differing only in
  `pref_ema` → action sequences must follow their own state-implied argmax
  direction with agreement ≥ 0.90 each, and differ from each other on ≥
  0.50 of ticks; `zeroed` ablation → agreement with original actions falls
  to ≤ 0.40. (Floors are design-verifiable for the constructed probe, set
  before implementation; if the implementation cannot meet them, that is a
  failed gate, not a floor to lower.)
- **G-R0-SEED-NEGCTRL** (detector must be able to fail): perturb one
  registered seed in the serialized state → replay MUST report mismatch;
  drop `noise_user` from the seed registry (simulated unseeded framework) →
  fresh-process replay x2 MUST detect nondeterminism. A blind detector =
  `instrument_invalid`, card fails.
- **G-R0-LLMSWAP-HARNESS** (skeleton): harness runs the probe behind two
  DETERMINISTIC stub renderers (pure functions that re-style the action
  into different "utterances"); state-attributed action deltas (from
  G-R0-CAUSALITY pairs) must be identical under both renderers; renderer
  identity must be recoverable ONLY from surface text, never from the
  kernel trace fields. Real-LLM enforcement is R3-adoption scope.
- **Hygiene gates**: no `EgoOperator` import anywhere in `scripts/ego_kernel`;
  no modification to `EgoDesktop/**` or `EgoOperator/**`; default-off scan
  (PSPC pattern) over both = 0 references; pytest green; verify scripts 4/4;
  admission-tools regression untouched (`tests/test_joi_corpus_admission.py`
  still green).

## Artifacts (evidence contract)

```text
artifacts/ego_r0_kernel_state_substrate_001a/
  result.json                # verdict + all gate outcomes + claim_ceiling
  config_frozen.json         # the predeclared run plan, hashed
  trace samples (per episode jsonl)
  replay_report.json         # incl. fresh-process x2 + resume results
  state_causality_report.json
  seed_negctrl_report.json
  llm_swap_harness_report.json
  failure_manifest.json      # if anything fails; preserve, never patch
```

Verdict vocabulary: `r0_substrate_pass` | `r0_substrate_fail_<gate>` |
`instrument_invalid_seed_detector_blind`.

## Stop conditions

- any replay or resume mismatch (STOP; failure manifest; no tolerance edit);
- causality floors unmet (STOP; report — do not redesign probe post hoc);
- seed negative-control does not fire (instrument_invalid — hard stop);
- any need to touch EgoDesktop/src, EgoOperator, PSPC, gates/approval/
  transport/proactive paths → scope violation, STOP;
- verify scripts fail after commits (do not patch authority files).

## Rollback

Delete `scripts/ego_kernel/`, the runner, the test file, the task dir, the
artifact dir; revert the PROGRAM_STATE entry commit. Nothing else changes.

## Claim ceiling

`kernel_substrate_engineering_only`. A pass means: the substrate is
replay-valid, resume-valid, seed-disciplined, and state-causal ON THE
CONSTRUCTED PROBE. It proves nothing about any real mechanism, learning,
memory, initiative, the desktop pet's behavior, runtime integration safety,
user benefit, autonomy, selfhood, consciousness, or emotion. It does not
connect anything to the running product.

## Next actions authorized on `r0_substrate_pass`

1. Draft `EGO-R1-MEMORY-OWNERSHIP-001A` (per decision card order).
2. Draft the R3-adoption slice card (g_ablation loop adopts substrate).
3. Nothing else.
