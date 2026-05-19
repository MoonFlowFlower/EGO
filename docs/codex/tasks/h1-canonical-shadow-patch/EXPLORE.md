# H1 Canonical Shadow Patch - EXPLORE

> 仅在 research / verify / observation / proof / high-unknown 任务中强制使用。
> 每次实验后必须先更新本文件，再开始下一轮。

## Exploration mode

- enabled: yes
- why exploration mode is needed: 当前关键未知是 shadow isolation 是否真实成立，需要用最小 replay/bridge 实验做否证
- current framing: 用 canonical surface + namespaced shadow keys 做 telemetry derivation，再用 host bridge 验证它没有进入 live decision path
- success looks like: flag on 时出现 `shadow_h1` telemetry；flag off 时完全消失；follow-up public outputs 与 baseline 一致
- disallowed premature claims:
  - `H1 已 promoted`
  - `runtime efficacy passed`
  - `repo-level state should upgrade`

## Question reformulation

- original question: 把 H1 接进 canonical proto-self
- normalized question: 在 canonical kernel 里加入一个 rollback-safe shadow telemetry path，证明它不会改写 live public behavior
- why this framing is better: 先验证隔离与可采样性，避免在坏 framing 下直接实现“半激活”机制

## Hypotheses

### Hypothesis 1

- statement: namespaced shadow keys 可以保留 canonical state writeback，同时不被 live reducer / confidence summary 当成正式 public signal
- why plausible: 当前 live path 只在少数 reducer / meta 读这些 dict，过滤后边界清晰
- kill criteria: follow-up public outputs 因 shadow keys 发生差异
- smallest experiment: failure -> follow-up 两步序列下比较 flag off / flag on 的 `policy_hint` 与 `response_tendency`

### Hypothesis 2

- statement: EgoCore 可以只读 forward `shadow_h1` 到 `proto_self_context` 与 observation record，而不进入 prompt / delivery path
- why plausible: runtime 已有大量 `proto_self_context` 桥接字段，observation record 允许附加可选字段
- kill criteria: final turn state 无法保留 `shadow_h1`，或必须改 decision_engine 才能看见 telemetry
- smallest experiment: 伪 adapter 注入 `trace_payload.shadow_h1`，检查 runtime bridge 和 observation record

## Experiment log

### Cycle 01

- question: canonical patch 是否能保持 shadow-only
- framing used: canonical owner + namespaced shadow keys + live reducer filtering
- experiment: 实施最小 patch，并用 scoped replay/runtime tests 比较 flag off / flag on
- command / script / artifact:
  - `python3 -m py_compile ...`
  - `PYTHONPATH=OpenEmotion python3 -m pytest OpenEmotion/openemotion/proto_self/tests/test_h1_shadow_canonical.py OpenEmotion/openemotion/proto_self/tests/test_kernel_replay.py -q`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_runtime_v2_proto_self_runtime.py EgoCore/tests/test_runtime_mainline_observation.py -q`
  - `git diff --check -- <scoped files>`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- observed result: flag off 不产 `shadow_h1`；flag on 产 telemetry 且 follow-up public outputs 与 baseline 一致；EgoCore 只读桥接与 observation hook 生效
- what it proves: 当前 patch 可以保持 shadow-only，不需要退回 mirror-only trace integration
- what it does not prove: 不证明 runtime efficacy，也不证明 E4 样本已经充分
- what path is ruled out: direct canonical writeback without isolation
- decision for next step: close 当前实现 slice，进入单独的 E4 shadow sampling 任务

## Framing changes

- 2026-04-09: `promote H1 into canonical` -> `shadow-only canonical telemetry patch` / 原因是证据上限只有 E3，且必须先验证不扰动 live path / 影响是当前任务只做 telemetry, bridge, observation

## Candidate vs proof

- candidate_found: H1 可以作为 canonical shadow telemetry candidate
- proof_pending: 尚未证明 flag off/on 与 replay behavior 的隔离成立
- proof_passed: none
- remaining proof gap: live public behavior invariance、final turn state retention、observation hook visibility
