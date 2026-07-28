# Collision record — EGO-V2-P1-HIERARCHICAL-OUTCOME-DELTA-REPAIR-001C-R2

## Observed collision

R1's full conditional tensor fixed the representation mismatch identified in
001C, but enlarged each action's planning heads from `6+4+1+1` to
`6+(6x4)+1+1`.  Its committed evidence preserved exact replay while increasing
world-54 fresh recovery from the 001C `8.44--8.56s` range to
`17.30--17.66s`.  The balanced prediction stage was therefore correctly not
run.

A read-only profile of the archived world-54 database recomputed 118 commands,
including 115 `plan_action` calls, 95,450 `_expand_node` calls and 751,925 pose
prediction requests.  Under profiler overhead, `plan_action` accounted for
25.27 of 29.99 recovery seconds and `_expand_node` for 21.42 seconds.  Two
temporary, untracked exact-replay prototypes—action-bundle caching and
all-action node expansion—still took about `12.2s`, above the frozen `10s`
boundary.  This rejects the claim that one more small cache is sufficient.

## Candidate comparison

| Candidate | Evidence produced | Strongest cheap match | Leakage / hard-coding risk | Smallest falsifier | Expected failure |
|---|---|---|---|---|---|
| Relax recovery count/threshold or trust stored plans | A green performance report | Measurement weakening rather than faster exact replay | Critical | Re-run the original three-process full-replay contract | False pass with weaker provenance |
| Keep the full interaction and add local caches/batching | Same statistical model with less Python overhead | Temporary prototypes already preserve exactness | Low | Worst old context remains over 10s | Insufficient speedup and continued sparse estimation |
| Identified additive shared feature slope plus zero-sum outcome residual, updated by joint NLMS | Lower-dimensional conditional learning, exact replay, balanced prediction and runtime evidence | Legacy unconditional model or no-update | Moderate shared-base spillover; low hidden-label risk | Late balanced MAE fails, residual ablation is insensitive, or recovery remains slow | The additive form may underfit a genuinely outcome-specific feature slope |

## Selection

Select the hierarchical additive model.  It attacks the common cause of the
current collision: the full outcome-by-feature interaction is both expensive
inside every beam node and statistically sparse in rare `interact` outcomes.
Normalized LMS supplies a predeclared scale-normalized linear update over the
joint shared-plus-outcome feature rather than introducing separate tuned
learning rates. A prediction-invariant sum-to-zero reparameterization removes
the base-bias/outcome-offset alias; no shrinkage prior is added, so this task
does not claim Bayesian partial pooling.

Reject threshold relaxation and stored-plan/checkpoint shortcuts because they
weaken the evidence contract.  Reject another cache-only patch because two
exact untracked prototypes remained above the frozen bound.  Reject a neural
candidate at this stage because the existing development gate has not yet
established headroom over explicit equal-access controls.

## Baseline, ablation and hostile checks

- Legacy unconditional delta and no-update are callable controls.
- Zero-residual evaluation retains the learned shared base and removes only
  outcome-specific offsets.
- The actual observed outcome may update its residual; prediction cannot read
  outcome, hidden object identity, cause/token mapping, seed, global position,
  or future observation.
- A shared base legitimately changes every conditional prediction. The
  sum-to-zero gauge projection also changes every serialized residual while
  preserving every pre/post-projection conditional value. The falsifier is a
  projection that changes those values, or zeroing/permuting residuals failing
  to change a conditioning-sensitive metric.
- Exact replay must recompute plans; cached or persisted plans are forbidden
  inputs.
- A greener survival trace, UI animation, passing unit tests, or a generated
  artifact cannot substitute for balanced prediction and held-out comparison.

## Stop and claim boundary

This task consumes no fresh effect seed.  If the hierarchical model misses the
old-context runtime or balanced gate, preserve the bounded negative result and
reframe; do not add another learning-rate/threshold patch.  A positive result
only permits authoring a separate frozen held-out effect card.  It is not
evidence of general learning, neural self-formation, agency, subjectivity,
consciousness, AGI, or electronic life.
