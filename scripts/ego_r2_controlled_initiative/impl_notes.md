# EGO-R2-CONTROLLED-INITIATIVE-001A I1 implementation notes

These notes freeze implementation constants not numerically fixed in the
landed card before any P0/P2 gate run.

- `x1` histogram bins: ten equal-width bins over `[0,1]`, matching the
  card's L2 10-bin requirement and avoiding any post-observation tuning.
- Phase map bins: fifty 10-tick bins over the 500-tick episode, matching the
  card's 50-bin L1 map.
- Phase estimator smoothing/history: the learner uses the last at most 80
  observed `(t,x2)` samples and picks the frozen grid offset minimizing
  squared error to the known carrier form. The first 12 ticks use offset `0`
  as a deterministic cold-start default.
- Belief fusion weights: L1 phase evidence and L2 x1 evidence are combined
  as `0.55 phase + 0.45 x1`, giving the integrable schedule carrier slight
  priority without allowing it to dominate the noisy direct proxy.
- Feedback fusion: an accept gives a 20-tick local high-receptivity boost;
  a reject gives a 50-tick low-receptivity suppress/backoff window. These
  values match the environment's positive/negative dynamics order of
  magnitude and are fixed before P0.
- Probe uncertainty rule: probes are allowed only when fewer than 150 ticks
  have elapsed, fewer than three probes were used, the phase table remains
  weakly separated (`abs(phase_hi - phase_lo) < 0.25`), and `p_lo < 0.2`.
- Decoder and distillate optimizers: fixed 120-step batch logistic gradient
  descent with learning rate `0.5`; no adaptive search, no hyperparameter
  sweep, and no post-P0 modification.

Changing any of the above after the first P0 run voids affected runs under
card K-F.
