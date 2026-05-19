# H1 Canonical Promotion Prep - STATUS

## Current milestone

- name: `M2: Host bridge + E4 prep`
- owner: `Codex`
- state: completed
- type: planning

## Current state

- current_layer: `planning_preimplementation_shadow_prep_complete`
- main_chain_status: `not_connected_by_design`
- completion_class: `closed`
- candidate_vs_proof: `proof_pending`

## Completed work

- `M0` 已完成并以 `continue` 收口：
  - 判断结果：`H1` 可以在现有 canonical proto_self surfaces 上表达，不需要 `canonical-contract-stabilization first`
- `M1` 已完成并以 `continue` 收口：
  - 已交付 `H1_TO_CANONICAL_MAPPING_SPEC.md`
  - 已交付 `CANONICAL_PATCH_PLAN.md`
- `M2` 已完成并以 `close` 收口：
  - 已交付 `FEATURE_FLAG_ROLLBACK_PLAN.md`
  - 已交付 `EGOCORE_FRONTEND_BRIDGE_PLAN.md`
  - 已交付 `E4_SAMPLE_COLLECTION_PLAN.md`
- 已补齐任务包：
  - `IMPLEMENT.md`
  - `EXPLORE.md`
- 全程未改：
  - repo-level program state
  - scorer ontology
  - Trial-1 / Trial-2 research artifacts

## Last experiment

- question:
  - H1 能否在不改变 host authority 的前提下，被翻译成 canonical proto_self 的最小 shadow-only promotion prep
- framing:
  - `canonical mapping + telemetry-only patch planning`
- result:
  - 可以
  - 但必须满足两个结构条件：
    - canonical H1 只能先落到 `shadow telemetry`
    - `decision_engine` 在这一阶段不能消费 H1
- evidence_upgraded: no

## What was learned

- canonical `SelfModel` 已具备 H1 需要的状态槽：
  - `counterfactual_success_by_action`
  - `recent_correction_tags`
- canonical `KernelOutput` 已具备 shadow rollout 需要的遥测面：
  - `confidence_meta`
  - `trace_payload`
- EgoCore 已具备最小 read-only bridge 面：
  - `state.proto_self_context`
  - runtime observation harness
- 当前真实结构风险在 reducer：
  - 直接 canonical 写入 H1 state 后，若不额外隔离，可能意外驱动 live `ask_preferred`

## What was ruled out

- 复用 `trial1_shadow.py` 作为 canonical owner implementation
- 新增 parallel proto-self engine
- 先改 scorer ontology 再做 canonical promotion
- 先把 H1 接回 `decision_engine.build_policy_hint_context()` 再说 shadow-only

## Next framing

- 若继续，应新开 implementation task：
  - `canonical shadow-only H1 telemetry slice`
  - 只实现最小 OpenEmotion patch + EgoCore read-only bridge + E4 sample capture
  - 不做 runtime efficacy claim

## Last validation results

- mode: `planning-slice closeout`
- result: `conditional_pass`
- summary:
  - `git diff --check -- docs/codex/tasks/h1-canonical-promotion-prep` = pass
  - `python3 scripts/codex/verify_repo.py --mode fast` = pass
  - `python3 scripts/codex/verify_repo.py --mode full` 已启动并暴露与本 planning slice 无直接因果关系的全仓历史失败：
    - `tests/test_dashboard_server.py::*flow_detail*`
    - `tests/test_native_loop.py::test_native_loop_runs_tool_call_and_returns_reply`
    - `tests/test_developmental_writeback.py::test_real_telegram_mainline_turn_writes_developmental_projection`
    - `tests/test_doc_system_inventory_builder.py::test_doc_system_inventory_builder_generates_key_outputs`
  - 因此当前 closeout 口径维持为：
    - `planning slice closed`
    - 不是 `repo full gate clean`

## Decisions made

- decision 1:
  - `H1` 不需要 `canonical-contract-stabilization first`
- decision 2:
  - canonical promotion 第一阶段只能是 `shadow-only / flag-guarded / rollback-safe`
- decision 3:
  - EgoCore bridge 第一阶段只能做 telemetry forwarding，不做 prompt injection
- decision 4:
  - `Trial-1` / `Trial-2` 维持 closed, read-only evidence status

## Open risks

- 风险 1:
  - 若 future implementation 直接重用 Trial helper，会重新引入双重真相源
- 风险 2:
  - 若 future implementation 不先隔离 reducer 的 live public derivation，shadow patch 会误变成 host-active behavior
- proof gap:
  - 尚未落 canonical shadow patch
  - 尚未做 feature-flagged runtime bridge
  - 尚未收集 E4 样本
  - 尚无 runtime efficacy 证据

## Next step

- 唯一最高优先级动作：
  - 若用户批准继续，实现一个新的最小任务：只在 canonical `proto_self` 上增加 `shadow_h1` telemetry，并跑受控 E4 样本采集

## Commands run / evidence

- `git diff --check -- docs/codex/tasks/h1-canonical-promotion-prep`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `python3 scripts/codex/verify_repo.py --mode full`
- `docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2/STATUS.md`
- `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_DECISION_CURRENT.json`
- `OpenEmotion/openemotion/proto_self/state.py`
- `OpenEmotion/openemotion/proto_self/self_model.py`
- `OpenEmotion/openemotion/proto_self/reducers.py`
- `OpenEmotion/openemotion/proto_self/kernel.py`
- `EgoCore/app/runtime_v2/proto_self_runtime.py`
- `EgoCore/app/runtime_v2/decision_engine.py`
- `scripts/runtime_mainline_observation_common.py`
- `EXPLORE.md` Cycle 01-03
