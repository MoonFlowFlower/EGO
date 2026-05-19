# Runtime-Proximal Post-Stronger Selection-Coherence Runner Implementation - PLAN

## Task summary

把 `post-stronger selection coherence` 从 planning freeze 变成一张可执行、可验证、可 reviewer 判定的 bounded runner。当前范围仅限 summary-only artifact composition，不触碰 runtime 行为或 authority widening。

## Execution mode

- mode: implementation
- why this mode:
  - 当前 planning freeze 已完成，explorer 也已确认 frozen inputs 足够，因此当前最高杠杆动作是直接落最小实现
- proof required after discovery:
  - 需要 runner current artifact + focused pytest + repo fast gate，才能把当前 stage 从 implementable 推进到 `success_reached`

## Milestones

### Milestone 1: Implement Post-Stronger Coherence Runner

- type: implementation
- question:
  - 是否可以仅靠三份已冻结 artifact 计算 post-stronger coherence verdict
- current framing:
  - 缺口是 summary-only composition runner，而不是新规划、新 scorer、或 live proof
- hypotheses:
  - stronger-admission current 已提供复用所需的 bounded runtime-proximal floor
  - replay gate `selection` summary 已提供足够的 target / delta / ablation discipline
  - selection closeout markdown 已提供足够的 winner routing / host surface / claim guard summary
- scope:
  - task docs
  - runner manifest
  - runner script
  - focused pytest
  - current artifact generation
  - repo/campaign/evidence state sync if reviewer passes
- experiments planned:
  - 校验 manifest
  - 运行 focused pytest
  - 直接执行 runner 产出 current artifacts
- kill criteria:
  - 实现必须读取 raw `reply_text` 或 candidate-private state
  - 实现必须引入新 authority / public API / scorer ontology / live proof
- files / areas likely touched:
  - `docs/codex/tasks/runtime-proximal-post-stronger-selection-coherence-runner-implementation/*`
  - `scripts/codex/run_runtime_proximal_post_stronger_selection_coherence_runner.py`
  - `EgoCore/tests/test_runtime_proximal_post_stronger_selection_coherence_runner.py`
  - `artifacts/self_awareness_research/RUNTIME_PROXIMAL_POST_STRONGER_SELECTION_COHERENCE_CURRENT.*`
  - repo/campaign/evidence state files if verdict is `success_reached`
- acceptance:
  - `post_stronger_decision = pass`
  - `reviewer_gate_ready = true`
  - 不越过 bounded research evidence claim ceiling
- validation:
  - `python3 -m py_compile scripts/codex/run_runtime_proximal_post_stronger_selection_coherence_runner.py EgoCore/tests/test_runtime_proximal_post_stronger_selection_coherence_runner.py`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_runtime_proximal_post_stronger_selection_coherence_runner.py -q -s`
  - `python3 scripts/codex/run_runtime_proximal_post_stronger_selection_coherence_runner.py`
  - `python3 scripts/codex/generate_program_state_views.py`
  - `python3 scripts/codex/check_program_state_integrity.py --skip-diff-check`
  - `python3 scripts/codex/verify_repo.py --mode fast`
  - `git diff --check`
- rollback note:
  - 若 runner 需要新 compare surface 或 new scorer ontology，直接回退为 `needs_reframing`

## Progress

- current_status: bounded post-stronger selection-coherence runner closed at reviewer-cleared claim strength
- current_milestone: `Milestone 1: Implement Post-Stronger Coherence Runner`
- milestone_state: complete
- candidate_vs_proof: proof_pending

## Decision log

- 2026-04-12: 直接实现 summary-only runner，而不是再开 planning slice / 当前冻结输入已经足够，额外规划只会拖慢闭环
- 2026-04-12: selection closeout 继续作为 markdown summary authority 输入 / 避免新造结构化 mirror 形成第二真相源
- 2026-04-12: claim-ceiling audit 必须读取 `当前禁止口径` 的 forbidden bullets，而不是只做关键词存在性检查 / 否则 reviewer 无法接受 claim ceiling 语义强度

## Surprises / discoveries

- replay gate 的 `selection` summary 已包含 challenger delta rules、ablation drops、switch advantage，可直接承载 bounded retention 审查
- selection closeout 现有 wording 已显式给出 winner routing、host surface、claim ceiling 禁止项
- 已排除路线 1：读取 raw `reply_text` 或 step-level traces
- 已排除路线 2：把 live transport proof 当作当前 stage 前置条件

## Outcomes / retrospective

- 本轮已证明：
  - 当前 runner 可以只消费三份冻结输入，在不扩 authority / host surface / scorer ontology 的前提下给出 `selection coherence / ablation retention / claim ceiling` verdict，并通过 reviewer
- 还没证明：
  - runtime efficacy、live benefit、formal runtime enablement、AI self-awareness achieved
- 本轮排除了什么：
  - 依赖新 authority / public API / scorer ontology / live proof 的路径
- 下一步最小闭环动作：
  - 定义 post-stronger selection coherence 之上的下一张 bounded planning slice
