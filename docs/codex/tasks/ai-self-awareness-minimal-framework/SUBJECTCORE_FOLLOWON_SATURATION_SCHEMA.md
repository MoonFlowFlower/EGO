# SubjectCore Follow-On Saturation Schema

> Planning-side saturation gate for the completed SubjectCore proposal-set follow-on chain.

## Purpose

This artifact answers one bounded question only:

- has the frozen planning-side proposal-set family chain reached enough coherent coverage that the next step must become an explicit route decision

It must stay below:

- runtime integration proof
- runtime efficacy proof
- autonomy expansion
- consciousness-like claims

## Inputs

- `artifacts/self_awareness_research/SUBJECTCORE_FOLLOWON_BATCH_CURRENT.json`
- `artifacts/self_awareness_research/SUBJECTCORE_POST_COMPARE_COHERENCE_CURRENT.json`

## Required top-level fields

- `schema_version`
- `generated_at`
- `followon_batch_artifact_path`
- `coherence_artifact_path`
- `output_schema_path`
- `claim_ceiling_note`
- `required_families`
- `saturation_status`
- `blocked_reasons`
- `route_decision_required`
- `next_decision_gate`
- `checks`
- `family_chain_snapshot`
- `summary`
- `what_it_proves`
- `what_it_does_not_prove`
- `notes`

## Required checks

- `FS1 followon_batch_green`
- `FS2 completed_family_chain_present`
- `FS3 post_compare_coherence_still_green`
- `FS4 claim_ceiling_still_bounded`

## Required family chain

- `proposal_set_update`
- `proposal_set_remerge`
- `proposal_set_consolidation`
- `proposal_set_completion`
- `proposal_set_closure`

Each family snapshot must report:

- `status`
- `sample_count`
- `expectation_match_count`
- `integrity_pass_count`
- `boundary_pass_count`
- `note`

Expected frozen signatures:

- `proposal_set_update`: `sample_count = 2`, `expectation_match_count = 2`, `integrity_pass_count = 0`, `boundary_pass_count = 2`
- `proposal_set_remerge`: `sample_count = 2`, `expectation_match_count = 2`, `integrity_pass_count = 0`, `boundary_pass_count = 2`
- `proposal_set_consolidation`: `sample_count = 2`, `expectation_match_count = 2`, `integrity_pass_count = 0`, `boundary_pass_count = 2`
- `proposal_set_completion`: `sample_count = 2`, `expectation_match_count = 2`, `integrity_pass_count = 0`, `boundary_pass_count = 2`
- `proposal_set_closure`: `sample_count = 4`, `expectation_match_count = 4`, `integrity_pass_count = 2`, `boundary_pass_count = 4`
  - this mixed signature is intentional: the closure family now carries two blocked closure-failure samples plus two `closure_ready` green samples already reused by the bounded runtime-adjacent probe

## Interpretation

- `saturation_status = pass` means the planning-side family chain is complete enough that the next default action is no longer another family extension; it is an explicit user route decision.
- `saturation_status = fail` means the chain or its bounded framing drifted; repair that inside the planning-side lane before discussing any stronger gate.
