# Simulated Shadow H1 Mainline Sampling - PLAN

## Task summary

用 simulated Telegram 调用统一 ingress/egress contract，验证 canonical `shadow_h1` 是否能进入完整 simulated mainline bundle，并把 real E4 所需的 operator 依赖从当前实现验证里剥离。

## Execution mode

- mode: exploration
- why this mode:
  - 当前核心问题不是“多写功能”，而是定位 bundle capture fidelity、task-conflict 污染和 subject-profile suppression
- proof required after discovery:
  - 完整 sample manifest + appearance/failure report + scoped verification

## Milestones

### Milestone 1: Stabilize simulated harness

- type: exploration
- question:
  - frozen prompts 为什么没有走到各自 intended path？
- current framing:
  - 先排掉 task-conflict / autonomy residue，再看 bundle capture 是否取错阶段
- hypotheses:
  - session 继承了 active task/autonomy 残留
  - sample bundle 被 finalized/idle 覆盖
- scope:
  - `scripts/codex/run_h1_simulated_mainline_sampling.py`
  - `scripts/codex/h1_simulated_sampling_common.py`
- experiments planned:
  - 清 session execution residue
  - 让 simulated runner 直接走 unified ingress + native_loop，不引 autonomy run orchestration
  - 比较 bundle 中 `openemotion_result.event_id`
- kill criteria:
  - 若仍只能采到 task-conflict / idle-overwrite，当前 slice 关闭并回退为 harness-design report
- files / areas likely touched:
  - simulated runner / simulated report builder
- acceptance:
  - 4 条 frozen prompts 都走到 intended path，并产生完整 simulated bundles
- validation:
  - `python3 -m py_compile scripts/codex/run_h1_simulated_mainline_sampling.py scripts/codex/build_h1_simulated_sample_reports.py scripts/codex/h1_simulated_sampling_common.py`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_h1_simulated_mainline_sampling.py`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/build_h1_simulated_sample_reports.py`
- rollback note:
  - runner-only patch，可直接回退到上一版 harness

### Milestone 2: Diagnose canonical H1 visibility

- type: exploration
- question:
  - canonical `shadow_h1` 为何在 simulated bundle 中缺失？
- current framing:
  - 区分 runner capture 问题 与 canonical mainline/profile 问题
- hypotheses:
  - `seed_v0_2` subject profile 抑制了 H1
  - external-result event 本身有 H1，但 evidence bundle 没保留到目标拍
- scope:
  - `scripts/codex/run_h1_simulated_mainline_sampling.py`
  - direct debug against `build_external_result_event -> adapter.handle_event`
- experiments planned:
  - 对比 plain vs `seed_v0_2` external-result event
  - 让 simulated bundle 固定停在 external-result 拍
  - 去掉 state snapshot 继承的 `proto_self_subject_profile_override`
- kill criteria:
  - 若 plain canonical path 也无 H1，则关闭为 canonical-mainline blocker
- files / areas likely touched:
  - simulated runner / task docs only
- acceptance:
  - 正样本路径能在 bundle 里看到 `shadow_h1`，并明确记录 residual risk
- validation:
  - `python3 -m py_compile scripts/codex/run_h1_simulated_mainline_sampling.py`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_h1_simulated_mainline_sampling.py`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/build_h1_simulated_sample_reports.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 只改 harness；不改 real E4 task、scorer ontology、repo truth

### Milestone 3: Repair seed_v0_2 H1 compatibility

- type: exploration
- question:
  - 为什么 `seed_v0_2` external-result path 会压掉 canonical `shadow_h1`，以及能否在不改 live policy 的前提下补回 telemetry？
- current framing:
  - 把问题限定为 seed profile 的 observable-path compatibility；不要求 seed path 新增 H1 backing state，只修“已有 eligible state 也被压掉”的缺口
- hypotheses:
  - `seed_v0_2` 走 `seed_kernel`，绕过了 v1 `build_shadow_h1_summary`
  - seed `perceived` 缺少 `runtime_summary / h1_shadow_active / action_class_seed`
  - H1 observable-path 只接受 `tool_result`，而 seed external-result 是 `exec_result`
- scope:
  - `OpenEmotion/openemotion/proto_self/h1_shadow.py`
  - `OpenEmotion/openemotion/proto_self_v2/seed_kernel.py`
  - `OpenEmotion/openemotion/proto_self_v2/kernel.py`
  - `OpenEmotion/openemotion/proto_self_v2/tests/test_seed_profile_contract.py`
- experiments planned:
  - direct repro: compare plain vs `seed_v0_2` external-result with H1 flag on
  - patch seed `perceived` to carry H1 fields for `exec_result`
  - patch seed kernel output to attach canonical H1 summary/confidence meta without touching live policy
- kill criteria:
  - 若 seed path 需要新增第二套 shadow state 才能出 telemetry，则当前 slice 关闭并回退为 compatibility note
- files / areas likely touched:
  - canonical proto_self v2 seed path only
- acceptance:
  - 在 preloaded eligible shadow state 下，plain 与 `seed_v0_2` external-result path 都能暴露相同的 `shadow_h1`
  - non-tool seed paths 不新增 `shadow_h1`
- validation:
  - `python3 -m py_compile OpenEmotion/openemotion/proto_self/h1_shadow.py OpenEmotion/openemotion/proto_self_v2/seed_kernel.py OpenEmotion/openemotion/proto_self_v2/kernel.py OpenEmotion/openemotion/proto_self_v2/tests/test_seed_profile_contract.py`
  - `PYTHONPATH=OpenEmotion python3 -m pytest OpenEmotion/openemotion/proto_self_v2/tests/test_seed_profile_contract.py OpenEmotion/openemotion/proto_self/tests/test_h1_shadow_canonical.py -q`
  - `EGO_ENABLE_H1_CANONICAL_SHADOW=true EGO_H1_CANONICAL_SHADOW_ALLOWLIST=telegram:dm:456 PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 - <<'PY' ... plain vs seed external-result repro ... PY`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_h1_simulated_mainline_sampling.py`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/build_h1_simulated_sample_reports.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - remove seed-path H1 telemetry glue only; no live decision rollback needed

## Progress

- current_status: slice_complete
- current_milestone: Milestone 3
- milestone_state: verified_pass
- candidate_vs_proof: proof_pending

## Decision log

- 2026-04-10: 新开 sibling task，不继续把 real E4 operator ingress 缺口当作当前实现验证 blocker
- 2026-04-10: simulated harness 关闭 autonomy orchestration，只保留 unified ingress -> native_loop -> canonical proto_self -> egress 主线
- 2026-04-10: simulated bundle 固定停在 external-result 拍，避免 finalized/idle 覆盖目标 telemetry
- 2026-04-10: `seed_v0_2` subject profile 被证实会压掉 `shadow_h1`；当前 slice 显式清掉 session snapshot 中的 subject-profile override
- 2026-04-10: canonical `h1_shadow` 改为只在 eligible tool-result path 发 telemetry，negative-control `user_message` 不再产出 `shadow_h1`
- 2026-04-10: `seed_v0_2` suppression root cause 确认为 seed path 绕过 v1 H1 builder；seed `exec_result` 现已补齐 canonical H1 telemetry glue，仍保持 shadow-only

## Surprises / discoveries

- task-conflict 不是主问题，active run orchestration residue 才是
- `process_finalized_result/process_idle_check` 会覆盖 sample 的 `openemotion_result`
- plain canonical external-result path 有 `shadow_h1`，但 `seed_v0_2` path 没有
- 负控 `shadow_h1` 泄漏源头在 canonical gating：`user_message` 也被当作 observable path
- `seed_v0_2` 不是“与 H1 理论不兼容”，而是 seed `exec_result` path 缺少 H1 observable glue；补齐后可在 eligible shadow state 下复现 plain path telemetry

## Outcomes / retrospective

- 本轮已证明：
  - simulated Telegram 可以复用统一 ingress/egress contract 走 canonical mainline
  - 正样本路径在 non-seed canonical profile 下可看到 `shadow_h1`
  - current negative control no longer emits `shadow_h1`; simulated report now closes cleanly
  - `seed_v0_2` external-result path no longer suppresses eligible `shadow_h1`; plain/seed now match under the same preloaded shadow state
- 还没证明：
  - real Telegram / E4
  - runtime efficacy
  - `seed_v0_2` 会自己稳定生成 H1 backing shadow state
- 本轮排除了什么：
  - “缺失只是 task-conflict/idle overwrite 噪声” 这条解释
  - “negative control leak is only a report-layer bug” 这条解释
  - “`seed_v0_2` suppression is only a report-layer artifact” 这条解释
- 下一步最小闭环动作：
  - 若继续这条线，优先重开 real E4 sampling；否则单开一个 narrow task 诊断 seed path 是否需要/应该生成 H1 backing shadow state
