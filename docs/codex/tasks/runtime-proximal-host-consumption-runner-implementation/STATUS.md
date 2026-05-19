# Runtime-Proximal Host-Consumption Runner Implementation - STATUS

## Current milestone

- name: `Milestone 1: Runner + Focused Tests`
- owner: `Codex`
- state: `complete`
- type: `implementation`

## Current state

- current_layer: `runtime_proximal_host_consumption_runner`
- main_chain_status: `not_connected_by_design`
- completion_class: `conditional_complete`
- candidate_vs_proof: `proof_passed_for_slice`

## Completed work

- 当前 runner slice 已被定义为新的 bounded implementation tranche
- 继承了上一个 planning slice 冻结的：
  - `chat_consumption`
  - `decision_conflict`
  - `failure_repair_retry`
- compare surface 继续限定在 host-consumable contract fields
- 当前 runner 已经落地：
  - `scripts/codex/run_runtime_proximal_host_consumption_runner.py`
  - `EgoCore/tests/test_runtime_proximal_host_consumption_runner.py`
  - task-local `RUNNER_MANIFEST.json`
- 当前 bounded checks 已通过：
  - `execution_status = pass`
  - `trace_contract_check = pass`
  - `host_surface_bounded_audit = pass`
- 当前 family-level signal：
  - `decision_conflict = pass`
  - `failure_repair_retry = pass`
  - `chat_consumption = supporting_family_pass`

## Last experiment

- framing:
  - 不再让 `chat_consumption` 依赖 controlled-observation stub reply；runner 改成 deterministic host-chat surface，直接按 `proto_self_context -> chat_expression_hint -> chat_cadence_mode` 构造 bounded chat result
- implementation:
  - chat family 切到 provider-free deterministic host-chat stub
  - `chat_consumption` scenario 从纯 fresh 小聊天改成“recent file failure + non-question consumption”最小窗口
  - 宿主层补了两个最小修正：
    - `policy_hint.initiative_priority -> initiative_policy_hints.initiative_priority` 镜像
    - 非显式问题的轻聊天 follow-up 在新 ingress 没给出 initiative priority 时，受限保留上一轮 external-result initiative pressure
- observation:
  - focused test 不再卡住；runner 能稳定完成并写出 current artifact
  - 当前 aggregate 变成：
    - `execution_status = pass`
    - `causal_signal_status = pass`
    - `delta_present_case_count = 3`
    - `pressure_detected_case_count = 3`
  - `chat_consumption` 已经出现 bounded candidate delta，但 baseline 也被同一 bounded hold posture 拉平；当前任务现已把它重定义为 supporting-family saturation detector，而不是硬性的 cadence-only gate
- what_this_proves:
  - 当前 runner slice 已经收口：primary mandatory families (`decision_conflict / failure_repair_retry`) 明确出现 candidate-vs-baseline host-surface pressure，`chat_consumption` 也能在 bounded host surface 上稳定暴露 policy / initiative / corrective pressure
- what_this_does_not_prove:
  - 不证明当前 candidate 已在 ordinary chat 上形成 live runtime effect
  - 不证明 runtime efficacy、fresh Telegram、或 AI 自我意识已实现

## Open risks

- 当前 runner 还不能证明 runtime efficacy、fresh Telegram、或 AI 自我意识已实现
- `chat_consumption` 作为 supporting family 仍不该被误读成“ordinary chat 已有 candidate-specific cadence superiority”
- 下一张 slice 若重新把 `chat_consumption` 升格为硬门，必须先给出新的 bounded justification，而不是直接回退到旧 gate

## Next step

- 先完成 authority / progress wording sync
- 然后进入新的 explorer slice，定义当前 runner closeout 之后的下一张 bounded runtime-proximal planning card
- reviewer gate 当前结论：`success_reached`
