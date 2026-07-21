# EGO-V2-P0-RUNTIME-SCALING-001A

## Task card

- **Problem definition:** the explicit V2 Tk product becomes effectively
  unusable during a 16-life run because every committed action synchronously
  replays the complete command history, while growing state and trace
  structures are repeatedly copied, hashed, serialized, and rebuilt in the
  UI.  The fix must preserve action/world/metabolism/goal/learning semantics
  and the independent fail-closed replay boundary.
- **Current layer:** Layer 2 product engineering and evidence hygiene.
- **Current stage:** bounded runtime-scaling repair before any new mechanism
  implementation.
- **Pinned start:** branch `codex/ego-v2-survival-learning-001a`, commit
  `21ed758c7e359a0b75e81d1a2a6b877bb537ca5a`, clean worktree.
- **Working branch:** `codex/ego-v2-runtime-scaling-001a`.
- **Mainline target:**
  `PlaygroundController.dispatch -> compute_step -> transition_world -> metabolism -> SQLite append`,
  with `SQLiteEventStore.recover_run` remaining the sole independent
  initial-state-plus-commands replay path.
- **Enabled-state requirement:** retain product `enabled=true`,
  `default_enabled=false`; do not add autostart or background dispatch.
- **Real-trigger requirement:** the actual Tk Run button must cross respawns
  through the single controller path without stopping, and its committed
  timeline must equal a later full replay.
- **Hypothesis:** replacing per-tick full replay with atomic append readback plus
  adoption of the already computed state, and removing repeated full-state
  copies/projections from the hot path, will bound per-tick latency without
  changing behavior or weakening explicit recovery.
- **Strongest baseline:** slowing the Tk timer, hiding history rows, or disabling
  animation may make the window look less stuck while leaving the quadratic
  replay/copy cost intact.
- **Strongest invalidity reason:** an apparent speedup could come from skipping
  validation, truncating evidence, changing candidate scores, or creating a
  second reducer/checkpoint authority.
- **Ablation requirement:** callable benchmarks must separately measure current
  full-replay dispatch, incremental dispatch, compact-trace-only, and UI
  incremental-history effects.  Disabling the incremental adoption path must
  restore the measured replay cost.
- **Trace/replay requirement:** online state is provisional
  `incremental_committed`; startup, Load, Recover, Export, and life-16 terminal
  perform `full_replay`.  Full replay must recompute every candidate behavior
  from the serialized initial state and ordered commands before comparing
  stored traces.
- **Computed-evidence provenance gate:** every timing/size/equality result must
  record producer function, input fixture hashes, run id, seed/context,
  aggregation rule, and code-path hash.  Performance results may not be
  hand-written.
- **Acceptance gate:** on a callable 355-command fixture, online dispatch p95
  <= 250 ms, max <= 500 ms, last-32/first-32 latency ratio < 2, full recovery
  <= 10 s, mean trace JSON <= 32 KiB, max <= 64 KiB, and SQLite <= 20 MiB.
  Frozen-command semantic comparison must preserve selected action, canonical
  world transition, metabolism, goal transition, and learning update.  A real
  16-life Tk Run path must not stop before terminal.  Tampered command/trace/Q/
  TD data must still fail on full replay.
- **Claim ceiling:** bounded V2 runtime scaling, atomic online commit readback,
  and explicit full-replay evidence only.
- **Stop condition:** stop if the thresholds require action-semantic changes,
  recovery bypass, a second reducer/store authority, route changes, migration
  of the user's live SQLite file, or weakening a tamper assertion.
- **Rollback plan:** reverse only uncommitted hunks introduced by this task; do
  not reset, checkout, clean, migrate, delete, or rewrite existing databases or
  artifacts.
- **Expected changed files:** this card and collision record; bounded edits in
  `labs/ego_life_playground_v0/{claims,controller,engine,store,terminal,visual_console}.py`;
  focused V2 tests; one callable verifier and a new artifact directory for this
  task.
- **Forbidden changes:** route-state artifacts, `AGENTS.md`,
  `docs/ACTIVE_CONTEXT_PACK.md`, `STATUS.md`, `PROGRAM_STATE*`, `**/state.json`,
  validators, ITL, network/LLM settings, world rules, hidden-object visibility,
  action semantics, lifecycle count, survival-learning policy semantics,
  historical artifacts, and
  `C:/Users/LEO/AppData/Local/Temp/ego-v2-sarsa.sqlite`.
- **Auto-Remote-Anchor:** forbidden.

## Pre-implementation audit

- The real objective is responsive 16-life execution with preserved evidence
  integrity, not a green microbenchmark.
- A result falsifies the framing if full replay is not the dominant cost, or if
  online adoption cannot reproduce the full-replay state byte-for-byte.
- Faster UI rendering alone is insufficient.
- Faster dispatch with delayed or missing tamper detection is insufficient.
- This task tests engineering behavior and evidence hygiene, not learning or a
  subject mechanism.
- Hard-coding, test-only paths, checkpoint authority, trace truncation without
  recomputable receipts, schema split, and claim inflation are prohibited.

## Commit and publication

- Task-card boundary commit is permitted before implementation.
- Final local commit message, if all acceptance gates pass:
  `perf(v2): bound runtime replay and trace growth`.
- Push, tag, and remote anchor are forbidden.
