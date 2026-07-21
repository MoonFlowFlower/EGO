# Collision Record — EGO-V2-P0-RUNTIME-SCALING-001A

## Observed collision

The user-visible symptom is an apparently stopped Tk run near sequence 355.
The live run has survival learning explicitly off.  Read-only inspection showed
355 command/trace rows, a 57,581,568-byte SQLite file, 56,838,998 trace JSON
bytes, 160,110 mean trace bytes, and 303,011 maximum trace bytes.  A copied
fixture required 66–80 seconds for full replay and 1.36 seconds for one current
`compute_step`.  These are diagnostic measurements, not a learning result.

## Candidate 1 — slow or simplify the renderer

- **Evidence produced:** a lower redraw rate or fewer visible history rows.
- **Cheap matching baseline:** user presses Pause/Run less often.
- **Leakage/hard-coding risk:** low, but it hides rather than removes compute.
- **Smallest falsifier:** headless dispatch at sequence 355 remains slow.
- **Expected failure mode:** full replay, state deepcopy, and trace growth still
  dominate.
- **Decision:** reject.

## Candidate 2 — checkpoint or cached-state recovery authority

- **Evidence produced:** fast restart from a persisted latest-state snapshot.
- **Cheap matching baseline:** trust the stored trace/state without independent
  recomputation.
- **Leakage/hard-coding risk:** high; a checkpoint can become a second reducer or
  bypass the initial-state-plus-commands boundary.
- **Smallest falsifier:** tamper with state and recompute its local hash; recovery
  accepts it without replaying prior commands.
- **Expected failure mode:** performance improves by weakening evidence.
- **Decision:** reject.

## Candidate 3 — one reducer, incremental online adoption, explicit full replay

- **Evidence produced:** bounded per-tick latency, exact row readback, and later
  byte-equivalent independent replay through the same `compute_step`.
- **Cheap matching baseline:** remove per-tick replay but leave state/trace copies
  growing; this may improve latency temporarily but fail the tail-growth gate.
- **Leakage/hard-coding risk:** online state could be mislabeled as recovered or
  compact receipts could omit recomputation inputs.
- **Smallest falsifier:** any frozen command selects a different action, any
  explicit recovery differs from online state, or a tampered trace is accepted.
- **Expected failure mode:** residual O(n) memory/claim work misses latency and
  trace-size thresholds.
- **Decision:** selected, with explicit verification-mode labeling and the
  original full replay retained as the only recovery authority.

## Frozen contract

- Online and recovery both call the same `compute_step`.
- Online state advances only after SQLite commit and exact row readback.
- No checkpoint is a replay input.
- Full replay remains mandatory at startup, Load, Recover, Export, and terminal.
- Behavior-bearing fields remain equal across the frozen fixture.
- Performance failure is reported as failure; thresholds and fixtures are not
  changed after observation.
- Claim ceiling remains runtime scaling and replay integrity only.
