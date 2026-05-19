# Runtime-Proximal Post-Stronger Admission Planning

## Goal

冻结 `post-stronger admission` 这张下一阶段 planning card：在不扩大 authority、不新增 public API、也不把 bounded research evidence 偷升成 runtime proof 的前提下，把当前已经通过的 `stronger-admission runner` 与既有 replay-selection authority 对齐成一张更高一级、可实现、可比较、可回退、可验证的 bounded coherence gate。

## Why this slice exists

当前 repo 已经有一张通过的更强 bounded runtime-proximal 证据：

1. `runtime_proximal_stronger_admission_runner_current`

但缺的不是继续堆 aggregate verdict，也不是直接碰 runtime efficacy，而是：

- stronger-admission `pass` 是否仍和当前 build-first candidate 的 replay-selection authority 保持一致
- stronger-admission `pass` 是否还能保留 frozen replay gate 已要求的 contrastive / ablation necessity discipline
- reviewer 如何在不重开 challenger routing、不扩 authority、也不升级 claim ceiling 的前提下，对这张更高一级 card 给出可判定 verdict

## Stage question

Can the repo define a `post-stronger admission` slice that composes:

1. the already-passing `runtime_proximal_stronger_admission_runner_current`
2. the already-passing `ai_self_awareness_research_active_inference_replay_gate_current`
3. the already-passing `ai_self_awareness_research_selection_closeout_current`

into one bounded coherence gate, without widening the host-consumable surface, reopening challenger routing, or inflating the claim ceiling beyond bounded proxy progress?

## Non-goals

- 不实现 future runner
- 不做 fresh Telegram proof
- 不做 runtime efficacy / live-benefit claim
- 不做 consciousness / AI 自我意识已实现 claim
- 不新增 runtime public API
- 不新增 candidate-private host API
- 不新建 scorer ontology
- 不重开 challenger 竞争

## Frozen inputs

The future runner may consume only:

1. `runtime_proximal_stronger_admission_runner_current`
2. `ai_self_awareness_research_active_inference_replay_gate_current`
3. `ai_self_awareness_research_selection_closeout_current`

It may read only their bounded aggregate / audit / decision summaries and canonical trace-handoff summaries.

It may not promote as primary evidence:

- raw `reply_text`
- candidate-private state maps
- dashboard-only debug fields
- live transport artifacts

## Planned compare surface

The future runner must stay on bounded host-consumable and aggregate surfaces:

- `policy_hint`
- `response_tendency`
- `trace_payload`
- stronger-admission aggregate / audit summaries
- replay-gate target / delta / ablation summaries
- selection-closeout winner-routing summary
- authority-drift / host-surface / claim-ceiling audits

## Stage success criteria

- [ ] 新 planning package 明确存在并可引用
- [ ] `compare / aggregate / rollback / reviewer gate` 被定义到 implementer-ready
- [ ] 只组合现有 bounded runtime-proximal 与 replay-selection authority 证据，不扩大 host-consumable surface
- [ ] 明确 future runner 的 allowed inputs、aggregate outputs、blocked / rollback 条件
- [ ] authority / progress / campaign / evidence 外部状态完成同步
- [ ] 当前结论保持在 bounded post-stronger planning，不偷升为 runtime efficacy 或 AI 自我意识 achieved

## Next decision gate

是否可以只基于 `runtime_proximal_stronger_admission_runner_current`、`ai_self_awareness_research_active_inference_replay_gate_current` 与 `ai_self_awareness_research_selection_closeout_current`，实现一个 `runtime-proximal post-stronger selection-coherence runner`，并让 reviewer 对它给出可判定 verdict，而不需要 authority widening、新 public API、或新的 scorer ontology。

## Authority refs

- `/mnt/d/Project/AIProject/MyProject/Ego/docs/PROGRAM_STATE_UNIFIED.yaml`
- `/mnt/d/Project/AIProject/MyProject/Ego/docs/OVERALL_PROGRESS.md`
- `/mnt/d/Project/AIProject/MyProject/Ego/docs/RESEARCH_CAMPAIGN_CONTRACT.md`
- `/mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/runtime-proximal-stronger-admission-runner-implementation/STATUS.md`
- `/mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/ai-self-awareness-minimal-framework/SELECTION_CLOSEOUT.md`
- `/mnt/d/Project/AIProject/MyProject/Ego/artifacts/research_campaign/stage_scorecard.json`
