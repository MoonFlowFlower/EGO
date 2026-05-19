# Runtime-Proximal Host-Consumption Causal Planning - STATUS

## Current milestone

- name: `Milestone 2: Scenario Bank + Compare Surface Draft`
- owner: `Codex`
- state: `complete`
- type: `exploration`

## Current state

- current_layer: `host_consumption_causal_planning_authorization`
- main_chain_status: `not_connected_by_design`
- completion_class: `planning_authorization_complete`
- candidate_vs_proof: `proof_pending`

## Completed work

- 新建 bounded planning package：`docs/codex/tasks/runtime-proximal-host-consumption-causal-planning/`
- 冻结 causal freeze artifact：`HOST_CONSUMPTION_CAUSAL_FREEZE.md`
- 冻结当前问题定义：不是继续做 host contract parity，而是判断 host-consumable outputs 是否能因果地改变宿主裁决与 reply 形态
- 冻结当前边界：
  - 不新增 runtime public API
  - 不新增 candidate-private host API
  - 不升级 live Telegram proof 为当前 acceptance root

## Last experiment

- question:
  - host contract correctness 之后，下一步是否应该切到 runtime-proximal host-consumption causal planning
- framing:
  - Telegram 只是 adapter；宿主 contract floor 已经冻结
- result:
  - next slice 应改为 planning-only causal freeze
- evidence_upgraded: `yes`

## Causal freeze artifact

- artifact: `HOST_CONSUMPTION_CAUSAL_FREEZE.md`
- frozen scenario families:
  - `chat_consumption`
  - `decision_conflict`
  - `failure_repair_retry`
- compare surface:
  - ingress semantics
  - `proto_self_context` host-consumable subset
  - `reply_authority`
  - `authority_source`
  - `delivery_kind`
  - `response_plan`
  - `response_tendency_summary`
  - `chat_cadence_mode`
  - `output_verdict`
  - `trace_payload`
- blocked / rollback:
  - no authority expansion
  - no new runtime lane
  - no candidate-private host API
  - no raw `reply_text` fallback as primary compare surface
- claim ceiling:
  - planning-only authorization

## What was learned

- host-contract parity 已经把 adapter-only 差异压到了 canonical floor 下面
- 下一步要回答的不是“有没有 contract”，而是“候选输出是否真能改变 host posture”
- 这一步仍然是 planning authorization，不是 runtime proof
- 三个最小 scenario families 已经固定，compare surface 也已经限死在 host-consumable contract 上
- reviewer 已把 scenario bank 收敛到真正覆盖 causal pressure 的 `decision_conflict` 与 `failure_repair_retry`，并移除了低信号文本主判据

## What was ruled out

- 继续把 fresh Telegram proof 当作当前唯一 acceptance root
- 直接把 causal planning 写成 runtime implementation

## Next framing

- 当前 next step：
  - 保持这张卡的 planning-only claim ceiling 不变
  - 把当前 execution owner 切到 `runtime-proximal-host-consumption-runner-implementation`
  - 不把这张卡升级为 runtime proof

## Last validation results

- mode: `docs/state only`
- result: `pass`
- summary:
  - `python3 scripts/codex/generate_program_state_views.py` pass
  - `python3 scripts/codex/check_program_state_integrity.py --skip-diff-check` pass
  - scoped `git diff --check` pass

## Decisions made

- 当前唯一 next slice：`runtime-proximal-host-consumption-causal-planning`
- `mandatory-subject-ingress-all-turns` 与 `live-chat-subjective-variability` 继续作为 downstream reference tasks
- 当前不请求 runtime code 变更

## Open risks

- 如果后续 runner 为了让 `chat_consumption` 过线而需要新增 authority path 或 candidate-private API，就说明 frozen framing 过宽，必须停下重定义
- 当前 planning 已完成，但这不等于 runner 已完成，更不等于 runtime proof

## Next step

- 把本 slice 维持为已完成的 planning authority
- 由 `runtime-proximal-host-consumption-runner-implementation` 继续承担实现与 reviewer 闭环

## Commands run / evidence

- `new_task.py` 创建 `docs/codex/tasks/runtime-proximal-host-consumption-causal-planning/`
- `python3 scripts/codex/generate_program_state_views.py`
- `python3 scripts/codex/check_program_state_integrity.py --skip-diff-check`
- `git diff --check -- docs/codex/tasks/runtime-proximal-host-consumption-causal-planning docs/codex/tasks/ai-self-awareness-minimal-framework/STATUS.md docs/codex/tasks/ai-self-awareness-minimal-framework/PLAN.md docs/codex/tasks/unified-host-contract-correctness/STATUS.md docs/PROGRAM_STATE_UNIFIED.yaml docs/OVERALL_PROGRESS.md docs/STATUS.md artifacts/reports/program_state_summary.md artifacts/evidence_ledger/index.yaml EgoCore/docs/PROGRAM_STATE_UNIFIED.yaml OpenEmotion/docs/PROGRAM_STATE_UNIFIED.yaml`
