# CARD A — egocentric visual ecology

- Task ID: `EGO-V2-P0-VISUAL-LIFE-CARD-A-001A`
- Problem: replace fixed semantic places, macro actions, and privileged policy
  inputs with the 5x5 visual/action/world contract in `PRODUCT_CONTRACT.md`.
- Layer: Layer 2 engineering plus bounded Layer 3 mechanism hypothesis.
- Mainline target: existing explicit launcher -> controller -> `compute_step` ->
  SQLite/recovery -> terminal/Tk path.
- Enabled requirement: `enabled=true`, `default_enabled=false`; no other
  enablement changes.
- Real trigger evidence: a real Step and Run commit must expose the exact policy
  visual array, one-cell/turn/interact transition, recovery, and UI redraw.
- Hypothesis: removing semantic/path access makes action selection depend on the
  stated local visual boundary rather than fixed sites.
- Strongest baseline: equal-access visual lookup/count controller; a privileged
  absolute-map planner is a leakage positive control, not a fair win.
- Ablation: memory-off, update-freeze, no-occlusion, fixed-position, and visual
  lookup baseline rerun callable episodes.
- Trace/replay: recompute observation, action, world transition, body delta,
  model/memory update, and hashes from initial state plus commands.
- Provenance gate: callable result/baseline/ablation/leakage/replay producers
  record inputs, run/seed/context/episode IDs, aggregation, and code hash.
- Acceptance: schema versions match the contract; five objects and hidden
  bijection exist; positions are deterministic and non-fixed; policy scan is
  clean and positive control fires; Step/Run/SQLite recovery use one path.
- Claim ceiling: local product ecology and evidence hygiene only.
- Stop: leakage, second logic path, nondeterministic sampling, replay mismatch,
  or requirement to migrate SQLite or touch control-plane files.
- Rollback: revert only this card's scoped local commit; preserve old artifacts.
- Expected files: `labs/ego_life_playground_v0/{microworld.py,engine.py,claims.py,controller.py,terminal.py,visual_console.py,__init__.py}`,
  `scripts/run_ego_life_playground_v0.py`, focused tests, one verifier and
  `artifacts/EGO-V2-P0-VISUAL-LIFE-CARD-A-001A/**`.
- Forbidden: ITL, route/status/program-state/validator files, SQLite migration,
  LLM/network/background paths, old artifact rewrites, push/tag/remote anchor.
- Local scoped commit requested: yes, after independent review.
- Auto-Remote-Anchor: `forbidden`.

The exact observation, action, sampler, occlusion, dynamics, UI split, versions,
and fail-closed rules are those in `PRODUCT_CONTRACT.md`; Card A may not tune
them after seeing results.
