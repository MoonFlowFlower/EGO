# Status

Last updated: 2026-06-01

## Result

`EGO-FS-097` is accepted as a local/scripted proof-chain rebaseline.

## Root Cause

The policy proof source chain was limited to the first 10 Functional Subject
trial cases. After recent first-pass/native-gate improvements, the first 10
cases no longer contain a `comparable_option_kind_mismatch` record with
`candidate_option_kind_mismatch` eligibility.

The tracked 20-case pack still contains one candidate-eligible target. The
proof chain failed because its source slice was too narrow, not because default
policy behavior is ready.

## Changes

- `run_functional_subject_candidate_eligible_feedback_replay_pack` now accepts
  `case_limit` and defaults to the full tracked pack.
- `run_functional_subject_feedback_runtime_ablation_proof` now defaults to the
  full tracked pack and passes that limit into the candidate-eligible source
  pack.
- The CLI exposes optional
  `--policy-human-sanity-review-path` and
  `--policy-real-provider-observation-path` for the default-enablement proof.
- Regression test added:
  `test_candidate_eligible_feedback_pack_uses_full_tracked_pack_by_default`.

## Evidence

Commands:

```bash
python3 -m py_compile scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py

TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py -k 'candidate_eligible_feedback_pack_uses_full_tracked_pack_by_default or feedback_runtime_ablation_proof_is_isolated or policy_default_enablement_proof_keeps_default_off or policy_reviewer_packet_holds_default_enablement'

python3 scripts/run_ego_experience_trial.py \
  --functional-subject-policy-opt-in-proof-arm \
  --out /tmp/ego_fs097_policy_opt_in_proof_arm_rebaseline

python3 scripts/run_ego_experience_trial.py \
  --functional-subject-policy-reviewer-packet \
  --out /tmp/ego_fs097_policy_reviewer_packet_rebaseline

python3 scripts/run_ego_experience_trial.py \
  --functional-subject-policy-default-enablement-proof \
  --policy-real-provider-observation-path /tmp/ego_fs010_functional_subject_total_gate_after_fs094_loop123b/functional_subject_trial_report.json \
  --out /tmp/ego_fs097_policy_default_enablement_proof_with_latest94_cli
```

Results:

- Targeted pytest: `4 passed`.
- `/tmp/ego_fs097_policy_opt_in_proof_arm_rebaseline/policy_opt_in_proof_arm_report.json`
  -> `scripted_policy_opt_in_proof_arm_pass`, target improved `1`, rollback
  disabled arm calibration count `0`.
- `/tmp/ego_fs097_policy_reviewer_packet_rebaseline/policy_reviewer_packet_report.json`
  -> `scripted_policy_reviewer_packet_pass`, default enablement allowed
  `false`, human sanity required `true`.
- `/tmp/ego_fs097_policy_default_enablement_proof_with_latest94_cli/policy_default_enablement_proof_report.json`
  -> `scripted_policy_default_enablement_proof_partial`, with source opt-in
  pass, proof arm calibration applied, latest #94 observation pass, and only
  human sanity checks remaining false.

## Decision

The proof chain is reproducible again from tracked inputs. Default enablement
remains blocked because the default-enablement proof still lacks current human
sanity evidence for this proof packet.

## Next Smallest Safe Step

Either attach/reconstruct current human sanity evidence for the default
enablement proof packet, or prioritize #94 human sanity / longer lifestyle
trial before default policy enablement.

## What This Does Not Prove

This does not prove default enablement, runtime efficacy, stable real user
benefit, live autonomy, durable memory efficacy, independent personhood, real
subjective experience, consciousness, or #94 closeout.
