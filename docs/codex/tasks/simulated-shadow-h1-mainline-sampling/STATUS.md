# Simulated Shadow H1 Mainline Sampling - STATUS

## Current milestone

- name: Milestone 3 - Repair seed_v0_2 H1 compatibility
- owner: Codex
- state: verified_pass
- type: exploration

## Current state

- current_layer: implementation verification / simulated mainline evidence
- main_chain_status: unified ingress/egress -> native_loop -> proto_self_runtime -> proto_self_adapter -> proto_self_v2 exercised in simulated Telegram harness
- completion_class: 条件性完成
- candidate_vs_proof: proof_pending

## Completed work

- built a simulated Telegram harness and report builder under `artifacts/telegram_simulated_mainline_v1/`
- removed task-conflict/autonomy contamination from the simulated slice
- froze bundle capture on the external-result stage for this harness
- isolated `seed_v0_2` subject-profile suppression from canonical H1 availability
- gated canonical `shadow_h1` to eligible tool-result paths only and eliminated negative-control leakage
- repaired seed `exec_result` compatibility so `seed_v0_2` no longer suppresses eligible `shadow_h1` telemetry

## Last experiment

- question:
  - `seed_v0_2` 为什么会压掉 external-result `shadow_h1`，以及能否在不碰 live policy 的前提下补回 canonical telemetry？
- framing:
  - 只修 seed `exec_result` observable-path compatibility；不扩 sample set，不新增第二套 shadow state
- result:
  - plain 与 `seed_v0_2` external-result path 在同一份 preloaded shadow state 下都能暴露相同 `shadow_h1`
  - non-tool seed path 仍不发 `shadow_h1`
- evidence_upgraded: no

## What was learned

- current simulated harness can produce 4/4 complete bundles on the intended path
- `shadow_h1` is present for `S1/S2/S4` and is guard-true for `S1/S4`
- `seed_v0_2` suppression root cause 是 seed path 绕过 v1 H1 builder，且缺少 `exec_result` observable glue
- canonical seed path 现在能在 eligible shadow state 已存在时暴露 `shadow_h1`
- canonical negative-control leak came from `build_shadow_h1_summary()` accepting ordinary `user_message` paths

## What was ruled out

- “sample failure is only caused by host task-conflict” 被排除
- “H1 is missing because finalized/idle overwrite is harmless” 被排除
- “canonical external-result path has no H1 at all” 被排除
- “negative-control leak is only a report-layer artifact” 被排除
- “`seed_v0_2` suppression is only a report-layer artifact” 被排除

## Next framing

- 当前 task 可收口；若继续，下一轮改成：seed path 是否需要/应该自己生成 H1 backing shadow state，而不仅是暴露已有 telemetry

## Last validation results

- mode: scoped scripts + repo fast verify
- result: pass
- summary:
  - `python3 -m py_compile OpenEmotion/openemotion/proto_self/h1_shadow.py OpenEmotion/openemotion/proto_self_v2/seed_kernel.py OpenEmotion/openemotion/proto_self_v2/kernel.py OpenEmotion/openemotion/proto_self_v2/tests/test_seed_profile_contract.py`
  - `PYTHONPATH=OpenEmotion python3 -m pytest OpenEmotion/openemotion/proto_self_v2/tests/test_seed_profile_contract.py OpenEmotion/openemotion/proto_self/tests/test_h1_shadow_canonical.py -q`
  - `EGO_ENABLE_H1_CANONICAL_SHADOW=true EGO_H1_CANONICAL_SHADOW_ALLOWLIST=telegram:dm:456 PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 - <<'PY' ... plain vs seed external-result repro ... PY`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_h1_simulated_mainline_sampling.py`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/build_h1_simulated_sample_reports.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`
  - `git diff --check -- OpenEmotion/openemotion/proto_self/h1_shadow.py OpenEmotion/openemotion/proto_self_v2/seed_kernel.py OpenEmotion/openemotion/proto_self_v2/kernel.py OpenEmotion/openemotion/proto_self_v2/tests/test_seed_profile_contract.py docs/codex/tasks/simulated-shadow-h1-mainline-sampling`

## Decisions made

- keep Trial-1 / Trial-2 read-only; use them only as evidence sources
- keep this slice simulated-only; do not upgrade repo-level state
- fix negative-control leakage in canonical H1 gating now that it is isolated to one observable-path function
- repair seed-profile suppression inside canonical seed path only; do not change live policy / response tendency / scorer ontology

## Open risks

- current harness proves simulated mainline only, not real Telegram / E4
- proof gap: no runtime efficacy claim, no repo-level enablement claim, and no proof that seed path self-generates H1 backing shadow state

## Next step

- if continuing, either resume real E4 sampling or open one narrow follow-up on seed-path H1 backing-state generation

## Commands run / evidence

- `python3 -m py_compile OpenEmotion/openemotion/proto_self/h1_shadow.py OpenEmotion/openemotion/proto_self_v2/seed_kernel.py OpenEmotion/openemotion/proto_self_v2/kernel.py OpenEmotion/openemotion/proto_self_v2/tests/test_seed_profile_contract.py`
- `PYTHONPATH=OpenEmotion python3 -m pytest OpenEmotion/openemotion/proto_self_v2/tests/test_seed_profile_contract.py OpenEmotion/openemotion/proto_self/tests/test_h1_shadow_canonical.py -q`
- `EGO_ENABLE_H1_CANONICAL_SHADOW=true EGO_H1_CANONICAL_SHADOW_ALLOWLIST=telegram:dm:456 PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 - <<'PY' ... plain vs seed external-result repro ... PY`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_h1_simulated_mainline_sampling.py`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/build_h1_simulated_sample_reports.py`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `git diff --check -- OpenEmotion/openemotion/proto_self/h1_shadow.py OpenEmotion/openemotion/proto_self_v2/seed_kernel.py OpenEmotion/openemotion/proto_self_v2/kernel.py OpenEmotion/openemotion/proto_self_v2/tests/test_seed_profile_contract.py docs/codex/tasks/simulated-shadow-h1-mainline-sampling`
- reports:
  - `artifacts/telegram_simulated_mainline_v1/reports/H1_SIMULATED_RUN_CURRENT.json`
  - `artifacts/telegram_simulated_mainline_v1/reports/H1_SIMULATED_SAMPLE_MANIFEST_CURRENT.json`
  - `artifacts/telegram_simulated_mainline_v1/reports/H1_SIMULATED_SHADOW_APPEARANCE_REPORT_CURRENT.json`
  - `artifacts/telegram_simulated_mainline_v1/reports/H1_SIMULATED_FAILURES_TABLE_CURRENT.json`
  - `artifacts/telegram_simulated_mainline_v1/reports/H1_SIMULATED_SAMPLE_LEVEL_REPORT_CURRENT.json`
