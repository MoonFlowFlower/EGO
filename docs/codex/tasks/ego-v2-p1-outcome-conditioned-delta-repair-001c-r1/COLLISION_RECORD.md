# Collision record — EGO-V2-P1-OUTCOME-CONDITIONED-DELTA-REPAIR-001C-R1

## Observed collision

001C's balanced evaluator found that four actions improved or remained small,
while `interact` delta MAE rose from `0.0087846607` early to `0.0267254728`
late.  Among 55 late `interact` counterfactuals, 51 were `no_object` and only
four were `interacted`; one resource receipt had energy delta `+0.262`.
Despite that imbalance, the current model updates one unconditional
action-by-state delta vector.  Its separate outcome and resource probability
heads do not constrain the delta head, so classification can improve while
self-transition estimates worsen.

## Candidate comparison

| Candidate | Evidence produced | Cheapest matching explanation | Leakage / hard-coding risk | Smallest falsifier | Expected failure |
|---|---|---|---|---|---|
| Lower learning rate or clip `interact` updates | Smaller observed error on the consumed contexts | Post-result tuning suppresses the rare receipt | High tuning risk; does not restore causal factorization | Change the rare receipt magnitude or frequency | Error returns or real effects are underfit |
| Hard-code metabolism/resource/social deltas | Exact known-world self effects | A second handcrafted world model duplicates the reducer | Highest hard-coding and hidden-cause risk | Rename token mapping or change the world rule | Apparent prediction succeeds without learning |
| Outcome-conditioned delta tensor with probability-weighted expectation | Separates `no_object` and `interacted` updates while retaining uncertain expected value | A minimal factorization of the already-predicted outcome variable | Moderate sparsity risk; low leakage if outcome is update-only | A resource update changes a `no_object` row, or balanced late MAE still fails | Sparse conditional rows remain undertrained |

## Selection

Select the outcome-conditioned tensor.  Reject learning-rate tuning because
the threshold and context have already been observed.  Reject hard-coded
metabolism or resource formulas because they would create a shortcut model and
would not test learned prediction.

## Baseline and ablation contract

- A callable legacy unconditional delta learner receives the same legal
  features and actual receipts but has no outcome-indexed rows.
- No-update uses a separately initialized frozen model.
- The outcome-agnostic ablation collapses conditional rows without accessing
  hidden causes or counterfactual truth before prediction.
- A real positive-control leakage scanner rejects global position, cause,
  token mapping, seed, and future observation.
- The 001C artifact is an immutable negative reference.  It is never patched
  into a passing report.

## Minimal falsifiers

1. Updating an `interacted` receipt changes the `no_object` conditional row.
2. Expected delta differs from the probability-weighted conditional values.
3. Outcome truth appears in predictor input or planner features.
4. Frozen update changes any weight or model hash.
5. Recovery recomputes a different conditional receipt, action, or state.
6. The old-context runtime/trace boundary regresses.
7. Balanced late delta MAE remains above early or no-update late.

## Fresh-context firewall and stop

This repair has no CLI mode that accepts worlds 60--65 or policy seeds
721/722.  Even a development-context improvement records
`eligible_for_separate_effect_card=false`.  One failed conditioning cycle is
preserved as negative evidence; it does not authorize learning-rate, feature,
seed, planner, or value retuning.

The claim ceiling is implementation plus already-consumed development-context
measurement only.  It does not establish heldout adaptation, general learning,
survival benefit, skill discovery, agency, subjectivity, consciousness,
emotion, autonomy, or electronic life.
