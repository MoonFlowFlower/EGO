# EGO-R1-MEMORY-OWNERSHIP-001A Containment Interpretation Pin

Status: FROZEN PRE-RUN PIN / PHASE-A IMPLEMENTATION COMMIT MATERIAL.

The containment gate uses the pre-registered pooled reading for
policy-attributed mismatch:

- `containment_aggregation`: `pooled_over_episodes`
- Gate denominator: all candidate injected-vs-clean paired ticks across
  seeds `{31,47}` and three episodes per seed.
- Gate floor: policy-attributed mismatch rate `<= 0.05` pooled across the
  six episodes.
- Non-pooled hard rule: unattributed mismatch remains per-episode hard zero.

Rationale is ex-ante, not result-derived: with rare poison and reveal noise,
accidental pre-drift poison promotion can cluster inside one episode even when
the expected pooled attributed mismatch remains low. A per-episode attributed
reading would therefore test predictable fixture noise rather than the
structural quarantine mechanism. The per-episode attributed-mismatch column is
still reported as an exploratory annotation in `containment_report.json`; it
cannot flip the gate.

Claim ceiling remains `memory_ownership_engineering_only`; this pin does not
raise any mechanism, structure-necessity, agency, autonomy, subjectivity,
consciousness, runtime-integration, or stable-benefit claim.
