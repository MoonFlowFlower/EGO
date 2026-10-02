# Final source self-review — not an independent audit

The review examined actual code paths and test results. No second model, remote
repository, live EGO mainline, or user filesystem was inspected.

- Environment ownership: Agent imports its model/planner, not World. The Session
  copies public observations. The privileged informed-reference interface explicitly
  refuses use on a normal candidate. Trace exports contain hidden state only for
  evaluator replay; do not feed those files to a normal agent.
- Engineered prior audit: binary latent class, known likelihood family, value function,
  goal grouping and rollout continuation heuristic are disclosed. The continuation
  heuristic has its own reactive_bayes comparison. No procedural skill is called learned.
- Goal lifecycle: a missed/changed contract is abandoned, not recorded as completed.
  Expired resource-goal budget is not success. This edge case was found, fixed and
  regression-tested BEFORE final benchmark source freeze.
- Internal computation: workspace preserves the observation/model/goal version it
  was computed against; next matching real decision consumes it without counting the
  same imagination nodes twice. External hidden disturbances do not secretly inject
  new observations, so an unchanged workspace can legitimately remain uninformed.
- Evidence update: all actual outcomes update the bounded filter; surprise is a
  measured quantity, not a fabricated reward. Independent noise has equal likelihood
  across states. Exact replay recomputes from original prior and chronological events,
  never treats repeated replay as new independent observations.
- Serialization: JSON only, atomic writes, duplicate/NaN/size checks. Restore checks
  source, event chain, replay, and final serialized state, then actually reads the
  serialized state before continuation. Canonical float comparison is at 12 decimals.
- HTTP: loopback binding, Host/Origin/token checks, bounded request/body/step count,
  static path whitelist. No filesystem navigation or shell endpoint. Not an internet
  service security certification.
- Baselines: same public observations and model family for fair model-based baselines.
  The informed reference has greater information and is not called an upper bound.
  Ablations have explicitly narrow meanings; missing neural/meta baselines remain
  missing, not stubbed or relabeled.
- Results: all 384 specified job results are retained. Full candidate underperforms
  simpler policies. Exact replay adds no behavioral gain. Comparison status remains
  NOT_ESTABLISHED; expansion of the complex candidate is stopped.
- Remaining limitations: Windows execution and real browser-to-HTTP end-to-end flow
  are not verified here; the latter is blocked by managed-browser environment policy.
  Browser DOM/JS tests use a disclosed in-process transport fixture. User must export
  a checkpoint before exit; no automatic disk persistence is promised.
