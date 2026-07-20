# CARD C — four-life lifecycle

- Task ID: `EGO-V2-P0-VISUAL-LIFE-CARD-C-001A`
- Problem: add death, pure respawn, four-life termination, 256-action-tick
  censoring, and exact carry/reset receipts inside `compute_step`.
- Layer: Layer 2 engineering plus bounded Layer 3 mechanism hypothesis.
- Mainline target: Card-B product path; `reset_run()` still starts a new trial.
- Enabled requirement: existing explicit local path, default off.
- Real trigger evidence: live continuous run reaches death/censor, commits a
  pure respawn command, and pauses at life-4 terminal state with survival output.
- Hypothesis: explicit reducer-owned lifecycle makes cross-life state transfer
  observable without a controller/UI state machine.
- Strongest baseline: controller-side respawn loop or scripted carry/reset.
- Ablation: full carry, full clear, model-only, memory-only, freeze-updates,
  memory exchange, and fixed-position variants remain later science work; Card C
  only verifies callable product carry/reset and a no-carry hostile check.
- Trace/replay: recompute death/censor/respawn/terminal transitions and every
  component hash from serialized initial state plus commands.
- Provenance gate: result summaries record producer, inputs, run/seed/context/
  episode IDs, aggregation, and code hash.
- Acceptance: four lives exactly; `episode == life`; zero energy blocks another
  policy action; respawn invokes no policy; carry bytes equal; reset bytes match
  the new-life constructor; life-4 dispatch rejection and fourth-life metric;
  fresh-process x2 and tamper fail-closed.
- Claim ceiling: local lifecycle, persistence, and replay integration only.
- Stop: fifth life, policy-visible life metadata, reset outside reducer, carry/
  reset mismatch, second state machine, replay mismatch, or SQLite migration.
- Rollback: revert only the scoped Card-C local commit.
- Expected files: `labs/ego_life_playground_v0/{engine.py,microworld.py,controller.py,terminal.py,visual_console.py}`,
  runner/UI focused tests, verifier extension, and
  `artifacts/EGO-V2-P0-VISUAL-LIFE-CARD-C-001A/**`.
- Forbidden: ITL/control-plane files, old artifact rewrites, LLM/network/
  background behavior, push/tag/remote anchor.
- Local scoped commit requested: yes, after independent review.
- Auto-Remote-Anchor: `forbidden`.

Carry exactly `model`, `memory.episodic`, `memory.consolidated`,
`memory.claim_events`, and `memory.competing_claims`. Reset body/world placement,
pose/orientation, per-life spawn counts, goal/latches, last action, life tick,
and working spatial state. The trial mapping, monotonically advancing life
index, and command/trace chains persist.
