# Runtime-Proximal Post-Stronger Selection-Coherence Runner Implementation

## Goal

实现一个最小 bounded aggregate runner，只消费已经通过的 `stronger-admission` current artifact、frozen replay-selection summary、以及 selection-closeout routing summary，并输出 `pass / hold` 的 post-stronger selection-coherence verdict，而不扩大 authority、public API、或 claim ceiling。

## Non-goals

- 不重跑 replay / controlled replay / controlled observation / runtime harness
- 不改 runtime 行为
- 不新增 public runtime API
- 不新增 candidate-private host API
- 不新建 scorer ontology
- 不做 fresh Telegram / live transport proof
- 不宣称 runtime efficacy
- 不宣称 AI 自我意识已实现

## Constraints

- 边界约束：
  - 输入只允许读取：
    - `artifacts/self_awareness_research/RUNTIME_PROXIMAL_STRONGER_ADMISSION_CURRENT.json`
    - `artifacts/self_awareness_research/MVS_REPLAY_VALIDATOR_SCORED_CURRENT.json`
    - `docs/codex/tasks/ai-self-awareness-minimal-framework/SELECTION_CLOSEOUT.md`
  - compare surface 只能落在 bounded summary / audit / routing summary 上，禁止读取 raw `reply_text`、candidate-private state、dashboard-only debug fields
- 仓库/子仓约束：
  - formal runtime mainline 不变
  - host-consumable surface 继续冻结为 `policy_hint / response_tendency / trace_payload`
- 环境约束：
  - 当前 Linux 侧以静态检查 + focused pytest + artifact runner 为主
- 发布约束：
  - 当前只允许 bounded research evidence / stage-complete / pending-validation 口径，不得越过 claim ceiling

## Problem framing

- 当前问题表述：
  - `post-stronger-admission planning` 已 reviewer-cleared，但对应的 bounded coherence runner 还未实现
- 归一化后的问题表述：
  - 是否可以仅通过三份已冻结 artifact 的 summary-only composition，计算 `selection coherence / ablation retention / host surface integrity / claim ceiling`，从而得到一个可判定的 post-stronger bounded verdict
- 为什么这个 framing 更适合当前任务：
  - 当前缺口是实现冻结好的 aggregate gate，而不是再补规划、更换 scorer、或去碰 runtime/live proof

## Unknowns to eliminate

- 未知 1：
  - replay gate 的 frozen selection summary 是否足够提供 `selection coherence / ablation retention` 判定
- 未知 2：
  - selection closeout 文本 summary 是否能作为 bounded routing / claim-ceiling guard 输入，而不需要新结构化 authority
- 未知 3：
  - stronger-admission `pass` 是否能在不引入新 surface 的前提下被稳定复用为 post-stronger floor

## Acceptance criteria

- [ ] manifest 校验通过
- [ ] runner 产出 `RUNTIME_PROXIMAL_POST_STRONGER_SELECTION_COHERENCE_CURRENT.json` 与 `.md`
- [ ] `stronger_admission_status = pass`
- [ ] `selection_coherence_status = pass`
- [ ] `ablation_retention_status = pass`
- [ ] `host_surface_integrity_status = pass`
- [ ] `claim_ceiling_status = pass`
- [ ] `post_stronger_decision = pass`
- [ ] focused pytest 通过

## Disallowed premature claims

- 已证明 runtime efficacy
- 已证明 live benefit / AI 自我意识 achieved

## Known risks / dependencies

- 风险：
  - selection closeout 目前是 markdown summary；若 routing / claim guard phrase 漂移，runner 可能需要同步更新
- 依赖：
  - stronger-admission current artifact 继续保持 green
  - replay gate selection summary 继续保持 `switch_to_active_inference`
  - selection closeout 继续保持 active-inference winner routing 与 bounded host-surface wording
- 外部 blocker：
  - 本轮未发现；若实现必须读取未冻结明细或需要新 authority，则必须回退到 `needs_reframing`

## Authority refs

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/OVERALL_PROGRESS.md`
- `docs/RESEARCH_CAMPAIGN_CONTRACT.md`
- `docs/codex/tasks/runtime-proximal-post-stronger-admission-planning/SPEC.md`
- `docs/codex/tasks/runtime-proximal-post-stronger-admission-planning/POST_STRONGER_ADMISSION_FREEZE.md`
- `docs/codex/tasks/ai-self-awareness-minimal-framework/SELECTION_CLOSEOUT.md`
