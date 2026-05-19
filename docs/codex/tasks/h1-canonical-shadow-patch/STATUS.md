# H1 Canonical Shadow Patch - STATUS

## Current milestone

- name: Milestone 2: Canonical Patch And Thin Bridge
- owner: Codex
- state: completed
- type: implementation

## Current state

- current_layer: Phase B / canonical proto_self shadow telemetry patch
- main_chain_status: canonical shadow telemetry wired on formal proto_self surfaces; no live decision promotion
- completion_class: conditional_complete
- candidate_vs_proof: proof_pending

## Completed work

- 新建 `docs/codex/tasks/h1-canonical-shadow-patch/` 长任务目录
- 重读前置 mapping / rollout / bridge / E4 sample planning authority
- 确认 `proto_self_v2` 默认经由 canonical v1 kernel，且当前 live reducer 必须先做 shadow isolation
- 实现 canonical `h1_shadow.py` helper、shadow-only reducer/meta isolation、v1/v2 trace telemetry
- 实现 EgoCore host-owned flag/allowlist、`proto_self_context["shadow_h1"]` 只读桥接、observation record hook
- 新增 scoped tests，验证 `flag off = no telemetry`、`flag on = telemetry only`

## Last experiment

- question: H1 能否作为 canonical shadow telemetry candidate 落进 formal proto_self surface
- framing: namespaced shadow keys + live reducer filtering + read-only EgoCore bridge
- result: patch shape成立并已落地；scoped replay/runtime checks 通过
- evidence_upgraded: no

## What was learned

- `counterfactual_success_by_action` / `recent_correction_tags` 一旦直写 live key，会直接污染 canonical public derivation
- 只要 final turn state 能保留 `shadow_h1`，现有 observation harness 就足以做 E4 shadow sampling

## What was ruled out

- 直接把 H1 接入 live `ask_preferred` / `ask_needed`
- 继续让 Trial-1 / Trial-2 runtime helper 充当 canonical owner implementation

## Next framing

- 把 H1 作为 canonical shadow telemetry 落进 state/trace/context 三个 surface，并用 scoped tests 证明 live public behavior 不变

## Last validation results

- mode: scoped implementation validation
- result: pass with full-gate residual repo failures
- summary:
  - `python3 -m py_compile ...` passed
  - OpenEmotion scoped pytest passed
  - EgoCore scoped pytest passed
  - scoped `git diff --check` passed
  - `python3 scripts/codex/verify_repo.py --mode fast` passed
  - `python3 scripts/codex/verify_repo.py --mode full` surfaced existing unrelated repo failures in `dashboard flow detail`, `native_loop`, `developmental_writeback`, `doc_system_inventory_builder`

## Decisions made

- 使用 host-owned feature flag + optional allowlist，OpenEmotion 不拥有 rollout authority
- 使用 namespaced shadow keys，而不是 live action key 直写

## Open risks

- 风险 1：当前只证明了 scoped shadow isolation，尚未收集 E4 formal-mainline 样本
- 风险 2：`shadow_h1` 目前是 telemetry candidate，不是 live efficacy signal
- proof gap: 还需要专门的 E4 sample collection 与 review task

## Next step

- 开单独任务采集 E4 controlled real-mainline `shadow_h1` 样本，并验证 rollback/allowlist discipline

## Commands run / evidence

- `python3 scripts/codex/new_task.py h1-canonical-shadow-patch --title "H1 Canonical Shadow Patch"`
- `python3 -m py_compile OpenEmotion/openemotion/proto_self/h1_shadow.py OpenEmotion/openemotion/proto_self/appraisal.py OpenEmotion/openemotion/proto_self/self_model.py OpenEmotion/openemotion/proto_self/reducers.py OpenEmotion/openemotion/proto_self/kernel.py OpenEmotion/openemotion/proto_self/trace_types.py OpenEmotion/openemotion/proto_self_v2/trace_types.py OpenEmotion/openemotion/proto_self_v2/kernel.py EgoCore/app/runtime_v2/proto_self_runtime.py scripts/runtime_mainline_observation_common.py OpenEmotion/openemotion/proto_self/tests/test_h1_shadow_canonical.py OpenEmotion/openemotion/proto_self/tests/test_kernel_replay.py EgoCore/tests/test_runtime_v2_proto_self_runtime.py EgoCore/tests/test_runtime_mainline_observation.py`
- `PYTHONPATH=OpenEmotion python3 -m pytest OpenEmotion/openemotion/proto_self/tests/test_h1_shadow_canonical.py OpenEmotion/openemotion/proto_self/tests/test_kernel_replay.py -q`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_runtime_v2_proto_self_runtime.py EgoCore/tests/test_runtime_mainline_observation.py -q`
- `git diff --check -- docs/codex/tasks/h1-canonical-shadow-patch OpenEmotion/openemotion/proto_self/h1_shadow.py OpenEmotion/openemotion/proto_self/appraisal.py OpenEmotion/openemotion/proto_self/self_model.py OpenEmotion/openemotion/proto_self/reducers.py OpenEmotion/openemotion/proto_self/kernel.py OpenEmotion/openemotion/proto_self/trace_types.py OpenEmotion/openemotion/proto_self_v2/trace_types.py OpenEmotion/openemotion/proto_self_v2/kernel.py OpenEmotion/openemotion/proto_self/tests/test_h1_shadow_canonical.py OpenEmotion/openemotion/proto_self/tests/test_kernel_replay.py EgoCore/app/runtime_v2/proto_self_runtime.py EgoCore/tests/test_runtime_v2_proto_self_runtime.py EgoCore/tests/test_runtime_mainline_observation.py scripts/runtime_mainline_observation_common.py`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `python3 scripts/codex/verify_repo.py --mode full`
- authority refs:
  - `docs/codex/tasks/h1-canonical-promotion-prep/H1_TO_CANONICAL_MAPPING_SPEC.md`
  - `docs/codex/tasks/h1-canonical-promotion-prep/CANONICAL_PATCH_PLAN.md`
  - `docs/codex/tasks/h1-canonical-promotion-prep/FEATURE_FLAG_ROLLBACK_PLAN.md`
  - `docs/codex/tasks/h1-canonical-promotion-prep/EGOCORE_FRONTEND_BRIDGE_PLAN.md`
  - `docs/codex/tasks/h1-canonical-promotion-prep/E4_SAMPLE_COLLECTION_PLAN.md`
- `EXPLORE.md` Cycle 01
