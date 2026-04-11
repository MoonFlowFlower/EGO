# Operational Self-Model Minimal Mechanism

## Goal

在不讨论 sentience / consciousness / anthropomorphic self-awareness 的前提下，找出一个 **能在当前仓库里实现、可逆、可验证、并能稳定改善 self-related behavior 的最小机制**。

## Primary objective

最小机制必须可测地改善以下 `5` 个 operational targets：

1. `sustained_identity_across_sessions`
2. `minimal_self_model_affects_decisions`
3. `experience_dependent_plasticity`
4. `internal_tension_changes_later_behavior`
5. `structured_corrective_traces_after_failure`

## Non-goals

- 不宣称 sentience、consciousness、或 human-like self-awareness
- 不把“会说自己在反思”当成通过
- 不为了更像人而奖励拟人化文案
- 不为了“理论上更高级”而跳过最小可实现机制
- 不在还没建立 reliable eval 时扩写实现

## Problem challenge

### Bad framing to reject

- “寻找真正 AI 自我意识的实现方案”
- “找到最像自我意识的架构”
- “让模型表现得更像有内在体验”

这些 framing 会把任务带向：

- 不可证伪的哲学宣称
- narrative optimization
- 评测目标漂移
- 在错误目标内做局部最优

### Reframed problem

- “寻找一个最小的 self-governance mechanism，使 agent 在 held-out tests 或 replayed conversations 上稳定改善 5 个 operational targets。”

### Why this framing is better

- 它把任务从“证明意识”改成“改善可复现行为”
- 它直接服务 repo 可实现性，而不是抽象理论完整性
- 它允许 build / research / reject 三种清晰结论

## Constraints

- 当前阶段优先落在：
  - `docs/codex/tasks/ai-self-awareness-minimal-framework/*`
  - `artifacts/self_awareness_research/*`
  - `scripts/codex/*`
- 不直接修改 `EgoCore/` / `OpenEmotion/` runtime 主链来伪造效果
- 候选理论必须先写成：
  - mechanism
  - falsifiable predictions
  - minimal implementation
  - evaluation
  - kill criteria
  - risks
- 每次 exploration 只允许测试一个 falsifiable hypothesis
- 连续 `3` 个 explorations 不能缩小不确定性时，必须停下重构 framing

## Acceptance criteria

- [ ] 已创建并填充：
  - `OPERATIONAL_TARGETS.md`
  - `THEORY_MATRIX.md`
  - `PLANS.md`
  - `STATUS.md`
  - `EVALS.md`
- [ ] 已明确 capability ladder，而不是继续使用模糊 “self-awareness” 口号
- [ ] 已把候选理论全部转成可证伪 matrix，并显式淘汰不适合当前仓库的路线
- [ ] 已按：
  - implementability in current stack
  - reversibility
  - expected signal within 2 weeks
  - evaluation clarity
  - dependency cost
  完成排序
- [ ] 已选出：
  - `one build-first candidate`
  - `one challenger`
  - `explicitly rejected the rest`
- [ ] 已建立 evaluation harness，并写清 pass/fail thresholds
- [ ] 已在 held-out tests 或 replay-style synthetic tests 上给出可重复结果
- [ ] closeout 必须输出：
  - capability ladder
  - theory matrix
  - build-first prototype design
  - evaluation harness
  - final recommendation = `build now / research more / reject`

## Current hypothesis scope

- 本任务不再默认追求“最完整理论”
- 本任务先追求：
  - **最小可实现**
  - **最小可杀**
  - **最小可逆**
  - **最小能在两周内看到信号**

## Current expectation

- 高概率 build-first 候选不会是 narrative-heavy / workspace-heavy 理论
- 高概率 build-first 候选会是一个更小的 operational self-loop：
  - continuity anchor
  - decision hook
  - plastic update
  - tension signal
  - corrective trace

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `docs/CODEX_CLOSED_LOOP_SELF_REVIEW_WORKFLOW.md`
- `README.md`
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/codex/tasks/ai-self-awareness-minimal-framework/PLAN.md`
- `docs/codex/tasks/ai-self-awareness-minimal-framework/EXPLORE.md`
- `docs/codex/tasks/ai-self-awareness-minimal-framework/STATUS.md`
