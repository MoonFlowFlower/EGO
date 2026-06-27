# EgoDesktop Joi Real-Loop G-ABLATION Wizard Captured Calibration Reference Replay Preflight v0 Status

## Current Milestone

- name: `Captured Reference Replay Preflight`
- owner: `Codex`
- state: `accepted_local`
- type: offline_artifact_preflight

## Current State

- current_layer: `engineering validation / captured calibration reference replay preflight`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `explicit_offline_artifact_runner_executed`
- real_trigger_evidence: `009_calibration_row_and_026_wizard_heldout_row_consumed_by_028_callable_scripts`
- completion_class: `local_preflight_artifact_pass`
- candidate_vs_proof: `preflight_proof_only_no_scoring_or_verdict`
- claim_ceiling: `wizard_captured_calibration_reference_replay_preflight_only`

## Current Readback

- branch at execution: `main`
- HEAD at execution start: `f8dc8556 docs: add wizard captured-reference replay card`
- 009 accepted calibration source row hash:
  `aebbdbedaca71d8955e470ffc6977d1bb9816e49f8af5878abd20eebbc5a4b28`
- 009 predeclared calibration prompt pack hash:
  `63704cafe002d3ee07f7b5a61a0f3820fca8688c9e52a844cd7d97600c7bc0db`
- 009 prior calibration reference hash, reference-only and not reused as final 028 evidence:
  `52411a8378e4a258a03f16b606052d9fcc42650af16c655684db07dc94356067`
- 026 Wizard heldout source row hash:
  `3a4569e77c39733a4d13034e3ad9cdfc5879e1974b9561760c06703e38d06a76`
- 028 captured calibration reference hash:
  `0c3c4ea74a06efd9a1f66136f5e06febf10affbf1553c38cc6bfadd2068aea27`
- 028 split partition manifest hash:
  `8d743ba6921272634dde4d3b0e229035dbd83f885efe6d1bdc4dfbff40202cb4`
- 028 replay row hash:
  `06df994805f6c8b6413e203929acb0e3d9cc2fa75237957a21d342de7161b4fd`

## Evidence Readback

- calibration builder status: `captured_calibration_reference_written`
- calibration reference kind: `captured_backend_trace_reference`
- selection policy status: `deterministic_predeclared_single_prompt_consumed`
- post hoc selection status: `absent`
- partition disjointness status: `pass`
- content disjointness status: `pass`
- provenance distinctness status: `pass`
- turn id provenance status: `informational_only_not_content_disjointness_gate`
- overlap positive control status: `pass`
- synthetic fallback positive control status: `pass`
- replay builder status: `off_static_replay_heldout_row_written`
- replay split contract status: `captured_calibration_reference_distinct_from_heldout_observation`
- heldout observation source hash:
  `3a4569e77c39733a4d13034e3ad9cdfc5879e1974b9561760c06703e38d06a76`
- evaluator status: `replay_integrity_preflight_pass_no_verdict`
- D-field replay precondition: `d_field_replay_precondition_satisfied=true`
- leakage scan status: `pass`
- leakage positive control status: `pass`
- scoring run authorized: `false`
- verdict authorized: `false`
- evaluator blockers: `[]`
- raw text field scan: `raw_text_field_scan_status=pass`

## Evidence Paths

- `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/calibration_reference/calibration_reference.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/calibration_reference/calibration_reference_report.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/calibration_reference/partition/SPLIT_PARTITION_MANIFEST.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/replay/builder_report.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/replay/trace_rows.jsonl`
- `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/eval/evaluation_report.json`

## Decisions

- The old 009 `calibration_reference.json` is not treated as Wizard-heldout-specific final evidence.
- The accepted 028 evidence is the new 028 partition/reference/replay/eval artifact set against the 026 Wizard heldout
  path.
- `turn_id` overlap remains informational only and is not used as a content-disjointness gate.
- Do not open scoring, same-access, `CREATURE_ON`, attribution, route advancement, program-state/evidence-ledger update,
  push, tag, or remote anchor.

## Validation / Closeout Log

- `python scripts\codex_session_guard.py bootstrap --format markdown`: pass; dirty total `0`, GitHub sync unavailable
  because `gh_not_found`.
- `node EgoDesktop/scripts/build-joi-g-ablation-calibration-reference.js ...`: pass.
- `node EgoDesktop/scripts/build-joi-g-ablation-off-static-replay-heldout.js ...`: pass.
- `node EgoDesktop/scripts/evaluate-joi-g-ablation-replay.js ...`: pass.
- raw-text field scan over 028 artifacts: pass.
- `python scripts\codex\verify_route_convergence.py`: pass; active default remains
  `ego-operator-human-operator-trial-v2`.
- `python scripts\sync_github_project.py plan --project-status --write-outbox`: pass locally with
  `EGODESKTOP-GABLATION-028` planned as closed/Done mirror operation; remote sync is not claimed because `gh` is not
  installed.
- 028 acceptance field assertion: pass.
- `python scripts\codex\verify_repo.py --mode fast`: pass.
- `git diff --check`: pass; Git reported only expected CRLF warnings.
- `python scripts\codex_session_guard.py --mutation-scope docs\codex\tasks\egodesktop-joi-real-loop-g-ablation-wizard-captured-calibration-reference-replay-preflight-v0\MUTATION_SCOPE.yaml closeout-check --format markdown`:
  scope loaded; dirty changes are scoped/task-scoped. Pre-stage blockers are `push_pending`, `no_staged_changes`, and
  `remote_sync_unavailable`; after scoped staging, remaining blockers are `push_pending` and `remote_sync_unavailable`.

## Next Step

Scoped stage and local commit. After this, the next minimal closed-loop action is a separate same-access baseline/scoring
contract task only if explicitly authorized; do not infer route advancement from this preflight.

## Current Claim Ceiling

This proves only Wizard captured calibration reference replay preflight. It does not prove `CREATURE_ON`, scoring,
same-access baseline, candidate attribution, route advancement, product benefit, runtime integration safety, stable user
benefit, durable memory efficacy, agency, emotion, subjectivity, consciousness, alive status, or Bar-2 specialness.
