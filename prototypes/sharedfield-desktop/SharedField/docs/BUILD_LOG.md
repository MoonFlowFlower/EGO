# Build ledger
- New isolated artifact workspace. No user repository is mounted or modified.
- User explicitly requested implementation of the preceding design and testing before
  delivery; this turn executes that request rather than requiring another design cycle.
- Scientific scope narrowed to the previously proposed first reference-controller stage.
  Neural learning/social/skills are not represented by stubs pretending to work.
- Development seed 41 exposed a design limitation: two-step candidate return 29.2,
  observation-only safe controller 45.2; candidate used 80/96 manual resource actions.
  Informed reference also returned 29.2. Thus the immediate problem is not merely
  state inference; a short continuation value undervalues amortized maintenance.
- Exact horizon probe at known damaged state (energy=5,coolant=4) retained manual
  collection at depths 2,3,4; root repair value rose but remained dominated. Full
  depth 4 used ~197k projection nodes per action. These are development diagnostics,
  NOT held-out results and NOT evidence for a scientific mechanism claim.
- Ruling: preserve original planner as `two_step`, keep environment/reward unchanged,
  add bounded particle-rollout MPC with a disclosed same-for-all continuation policy.
  This changes planning coverage, not the benchmark or evaluation gate. Flat Bayes
  gets the identical rollout mechanism; comparisons may still favor simpler control.
- Particle-rollout development probe (same seed 41): return 27.05, 4 completions;
  repair=4, calibration=2, world probes=3. It makes maintenance/diagnostic decisions
  but DOES NOT improve this seed's return over two-step (29.2) or safe rules (45.2).
  No reward, physics, seed exclusion or threshold changes were made. Preserve this
  negative result and compare the rollout continuation policy directly as reactive_bayes.
- First 384-job evaluation attempt hit the execution tool's 200-second wall timeout
  after 128 ordered job completions. No completed full benchmark or summary exists for
  that attempt; its contract and progress log are retained in benchmark_interrupted.
- Reliability fix: flush each completed independent-life row to rows.partial.jsonl;
  a later failure cannot erase earlier completed observations. Added a regression test.
- Performance-only refactor: action-cache copies use nested dict copies instead of
  generic deepcopy. The same eight-step witness gives identical outputs before/after.
  No environment, reward, planner, seed inclusion, or acceptance threshold changed.
- Evaluation will restart in this session with an updated recorded source fingerprint;
  the timed-out attempt is not represented as completed evidence.

- User-facing delivery paths: launchers, Chinese README, local dashboard, CLI, state export/resume, raw reports. No Windows execution claim.
