# Theory Matrix

## Ranking dimensions

- `implementability`
- `reversibility`
- `signal_within_2_weeks`
- `evaluation_clarity`
- `dependency_cost`

评分说明：

- `1` = 很差 / 很重 / 很模糊
- `5` = 很好 / 很轻 / 很清晰

## Candidate matrix

| candidate | mechanism | falsifiable prediction | minimal implementation | evaluation | kill criteria | risks | impl | rev | signal | eval | dep | verdict |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| Narrative identity shell | 通过 narrative continuity 与自述保持“像同一个体” | 若它有效，identity 与 corrective trace 应明显改善 | narrative summary + self-description prompt surface | T1 / T5 | 若只改善 wording，不改善 held-out behavior，则 kill | 强 anthropomorphic bias | 5 | 5 | 3 | 2 | 5 | reject |
| Global workspace self-slot | 用全局广播把自我状态暴露给多个过程 | 若它必要，decision impact 与 cross-context consistency 应明显领先更小机制 | workspace state + shared self slot + broadcast gate | T1 / T2 | 若 operational core 已足够，则不值得先做 | scope 容易膨胀 | 2 | 2 | 2 | 3 | 2 | reject for now |
| Corrective trace only | 失败后写 structured trace，但没有稳定 self state 或 tension loop | 若它有效，T5 会提升，但 T1-T4 不应明显改善 | failure record + source attribution + next guard | T5 | 若只改 failure logging，则不能作为主候选 | 只修尾部，不改主体 | 5 | 5 | 4 | 5 | 5 | reject |
| Social mirror loop | 通过 external-observer model 形成自我 | 若它必要，ownership attribution 与 tension regulation 会优于更小机制 | observer model + self/other feedback comparison | T2 / T4 | 若无社会反馈时无优势，则 kill | 高依赖外部反馈分布 | 2 | 3 | 2 | 3 | 2 | reject |
| MVS-aligned compact | 在 compact 核上补 viability / cycle / episodic / bounded output / world / meta | 若 operational targets 已经需要这些附加层，则应稳定优于更小 operational core | compact core + viability + cycle + episodic + world/meta | T1-T5 composite + robustness audit | 若收益边际小于实现成本，或 robustness 不足，则不做主线 | 结构比目标更宽 | 4 | 4 | 4 | 4 | 3 | provisional current best under current eval |
| Active-inference self-model | 在 MVS core 之上补 policy evaluation、uncertainty、deep temporal control | 若更深自我模型必要，它应在 T2-T4 持续领先 | MVS core + uncertainty + policy eval + deep temporal model | T2 / T3 / T4 + challenger switch criteria | 若 MVS compact 通过 robustness 且 build-first tradeoff 更好，则不做主线 | 依赖更重，实现更慢 | 3 | 3 | 3 | 4 | 2 | provisional backup / challenger |
| Operational self-loop core | continuity anchor + decision hook + plastic update + tension field + corrective trace | 若这是最小可行机制，它应以较低依赖成本通过全部 T1-T5 held-out thresholds | identity anchor + self-model decision hook + plastic writeback + tension state + corrective trace | T1-T5 all | 若任一 target 过不了，或只靠 wording 获胜，则 kill | 可能对更复杂 attribution 不够 | 5 | 5 | 5 | 5 | 5 | reject |

## Current ranking under existing eval setup

- `current best build-first candidate under current eval setup`: `MVS-aligned compact`
- 原因：
  - 它是当前 **最小过线候选**
  - 在 held-out operational eval 中通过全部 `T1-T5`
  - build-now score 高于 `active-inference self-model`
  - 仍然比更大的 active-inference 方案更接近当前 repo stack
  - 且现在已经通过：
    - `5` seeds
    - `3` held-out splits
    - `35` weight scenarios
    的 robustness audit

## Current challenger under existing eval setup

- `current backup / challenger under current eval setup`: `Active-inference self-model`
- 原因：
  - 它在 raw operational score 上更强
  - 如果后续需要更深的 tension / policy / uncertainty control，它是自然升级方向
  - 但当前不具备更好的 build-first tradeoff

## Required de-risking before implementation

- ranking robustness audit：
  - 已完成，见 [RANKING_ROBUSTNESS_AUDIT.md](/mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/ai-self-awareness-minimal-framework/RANKING_ROBUSTNESS_AUDIT.md)
- formal prototype design：
  - 已完成，见 [MVS_ALIGNED_COMPACT_PROTOTYPE_DESIGN.md](/mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/ai-self-awareness-minimal-framework/MVS_ALIGNED_COMPACT_PROTOTYPE_DESIGN.md)
- replay validator spec：
  - 已完成，见 [REPLAY_VALIDATOR_SPEC.md](/mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/ai-self-awareness-minimal-framework/REPLAY_VALIDATOR_SPEC.md)

## Explicit rejections

- `Narrative identity shell`: reject
- `Global workspace self-slot`: reject for now
- `Corrective trace only`: reject
- `Social mirror loop`: reject
- `Operational self-loop core`: reject as current build-now mainline

## Prototype design

### Mainline prototype

- `identity_anchor`
- `self_model_decision_hook`
- `plastic_writeback`
- `tension_field`
- `corrective_trace`
- `episodic_trace`
- `world_model`
- `meta_model`

### Backup prototype

- mainline prototype
- `uncertainty_tracker`
- `policy_evaluator`
