# CARD B — goal hysteresis and explore state

- Task ID: `EGO-V2-P0-VISUAL-LIFE-CARD-B-001A`
- Problem: replace immediate max-deficit retargeting with the fixed
  `0.72/0.60/0.15` target, latch, override, and explore contract.
- Layer: Layer 2 engineering plus bounded Layer 3 mechanism hypothesis.
- Mainline target: the Card-A `compute_step` scorer and existing recovered UI.
- Enabled requirement: existing explicit local path, default off.
- Real trigger evidence: live trace shows completion, carried target, explore,
  sub-0.60 reentry, severe override, and displayed transition reasons.
- Hypothesis: latches prevent oscillation while visual-transition counts provide
  a non-semantic exploration pressure.
- Strongest baseline: a fixed priority FSM or goal rotation with the same output.
- Ablation: no-hysteresis, no-novelty, and no-override reruns through the real
  reducer; equivalence is retained as negative evidence.
- Trace/replay: record goal before/after, deficits, latches, completion,
  transition kind, override reason, novelty counts/score, and hashes.
- Provenance gate: all summaries come from callable reruns and record producer,
  inputs, run/seed/context/episode IDs, aggregation, and code hash.
- Acceptance: focused RED/GREEN tests cover all transitions; replay and UI show
  the same reasons; no event name, absolute position, map/topology, path,
  legal-action mask, seed, life ID, or token-to-cause mapping affects goal
  selection.
- Claim ceiling: bounded goal-control implementation only.
- Stop: fixed rotation, threshold tuning after results, leakage, inert ablation,
  second goal path, or replay mismatch.
- Rollback: revert only the scoped Card-B local commit.
- Expected files: `labs/ego_life_playground_v0/engine.py`, terminal/Tk trace
  presentation as required, focused tests, verifier extension, and
  `artifacts/EGO-V2-P0-VISUAL-LIFE-CARD-B-001A/**`.
- Forbidden: Card-A contract changes, ITL/control-plane files, background/LLM/
  network behavior, old artifact rewrites, push/tag/remote anchor.
- Local scoped commit requested: yes, after independent review.
- Auto-Remote-Anchor: `forbidden`.

Current goal persists until its variable reaches `0.72`; a completed variable
reenters only below `0.60`. Any variable at or below `0.15` is severe; energy at
or below `0.15` takes priority. No eligible bodily deficit means `explore`.
