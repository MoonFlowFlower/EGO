# Trial-2 Public-Driver-First Spec - PLAN

## Task summary

这是一个 `bounded long-run` 的 Trial-2 任务。目标不是扩理论，而是在 **现有 scorer + 现有 hard set** 下识别：

- 当前 `MVS` public outputs 的真实 causal driver 是哪条 path
- 哪条假设该继续，哪条该降级
- 是否已经足够关闭本轮 Trial-2

当前范围只做：

- `M0` 问题冻结
- `M1` 最多 3 条 public-driver hypothesis 排名
- `M2` 最小判别实验设计
- `M3` 最小实现 + 同一 hard set rerun
- `M4` 决策

明确不做：

- replay-suite expansion
- challenger scoring
- scorer ontology 变更
- repo-level state upgrade

## Execution mode

- mode: exploration
- why this mode:
  - 当前核心问题不是“加更多机制”，而是“现有 scorer 真正看到的是哪条 public path”
- proof required after discovery:
  - 即使 Trial-2 识别出 bounded active public driver，也仍然只到 `E3`；没有 `E4` 真实主链样本前，不得报生效

## Stop conditions

- 若 public-driver candidate set 超过 `3` 条，立即停止并重定任务范围
- 若要得到区分必须改 scorer ontology 或 material change hard set，立即停止并记为 `rescope required`
- 若 `M2` 结束时仍没有最小判别实验，直接 `close as underdefined`

## Milestones

### M0: Problem Freeze

- type: exploration
- question:
  - 在不扩 hard set / scorer 的前提下，本任务到底要识别什么
- current framing:
  - `bounded public-driver identification`
- hypotheses:
  - H1 `counterfactual low-success guard` 是当前 bounded hard set 上最可能的 active public driver
  - H2 `correction-pressure public guard` 是候选，但当前更可能只是 latent path
  - H3 `viability-pressure public guard` 是候选，但当前更可能只是 latent path
- scope:
  - 冻结问题表述、hard constraints、stop conditions、candidate set、reject list
- experiments planned:
  - doc-only freeze
- kill criteria:
  - 若候选集超过 `3` 条，或 framing 仍回到“fix counterfactual_writeback”，当前 milestone 失败
- files / areas likely touched:
  - `docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2/*`
- acceptance:
  - `SPEC.md / PLAN.md / STATUS.md / EXPLORE.md` 明确锁定 bounded objective
  - 显式 reject 至少两条坏 framing
- validation:
  - `git diff --check -- docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2`
- rollback note:
  - 若 Trial-2 仍依赖聊天口头上下文而非 repo-tracked docs，则回退重写
- milestone end:
  - `continue`

### M1: Candidate Public-Driver Ranking

- type: exploration
- question:
  - 在当前 hard set 和 scorer 下，哪条 public path 最可能真实驱动当前 observable gap
- current framing:
  - `rank bounded active drivers, not universal theory`
- hypotheses:
  - H1 `counterfactual low-success guard`
  - H2 `correction-pressure public guard`
  - H3 `viability-pressure public guard`
- scope:
  - 用既有 Trial-1 artifacts 给出 `1 > 2 > 3` 的 bounded ranking，并明确 reject 项
- experiments planned:
  - artifact-only ranking
- kill criteria:
  - 若排名依赖新增 hypothesis、reflection-only 独立候选、或 scorer 变更，则当前 milestone 失败
- files / areas likely touched:
  - `docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2/*`
- acceptance:
  - 明确 `mainline / backup / tertiary / rejects`
  - 明确 ranking 只对当前 hard set 成立
- validation:
  - `git diff --check -- docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2`
- rollback note:
  - 若当前 artifact 已不足以给出 bounded ranking，则 `close as underdefined`
- milestone end:
  - `continue`

### M2: Minimal Discriminative Experiment Design

- type: exploration
- question:
  - 最小且不改 scorer/hard set 的实验是什么，能把三条 public-driver hypothesis 区分开
- current framing:
  - `split-sever only the public path under test`
- hypotheses:
  - `trial1_ablation_counterfactual_public_path_sever` 用于切断 H1
  - `trial2_ablation_correction_public_path_sever` 用于切断 H2
  - `trial2_ablation_viability_public_path_sever` 用于切断 H3
- scope:
  - 冻结 Trial-2 判别实验、预注册解释规则、输出 artifact 名称
- experiments planned:
  - 在 **现有 hard set** 上重跑：
    - baseline
    - candidate
    - `trial1_ablation_counterfactual_public_path_sever`
    - `trial2_ablation_correction_public_path_sever`
    - `trial2_ablation_viability_public_path_sever`
- kill criteria:
  - 若没有一个 split-sever 能忠实只切一条 public path，则当前 milestone 失败
- files / areas likely touched:
  - `docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2/*`
  - `OpenEmotion/openemotion/proto_self/trial1_shadow.py`
  - `EgoCore/tests/test_trial1_shadow_replay_minimal.py`
- acceptance:
  - scorer ontology 不变
  - hard set 不变
  - candidate set 仍然只有 `3` 条
  - 解释规则预注册为：
    - 若某个 sever ablation `mean_weighted_gap > 0.0` 且 `positive_gap_case_count >= 2`
    - 且其余 sever ablations `mean_weighted_gap <= 0.01`
    - 则该 path 记为当前 bounded active public driver
    - 否则本轮 `close as underdefined`
- validation:
  - `git diff --check -- docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2 OpenEmotion/openemotion/proto_self/trial1_shadow.py EgoCore/tests/test_trial1_shadow_replay_minimal.py`
- rollback note:
  - 若必须改 scorer 或换 hard set 才能区分，就按 stop rule 关闭
- milestone end:
  - `continue`

### M3: Minimal Implementation + Rerun

- type: implementation
- question:
  - split-sever 诊断变体在当前 hard set 上是否真能区分 active public driver
- current framing:
  - `minimum diagnostic slice only`
- hypotheses:
  - 若 H1 是当前 active public driver，则 only-H1 sever 会留下 public gap，而 H2/H3 sever 近似 candidate
- scope:
  - 只实现两个 split diagnostic ablations
  - 重跑现有 hard set
  - 用现有 scorer 计分
- experiments planned:
  - `py_compile`
  - 定向 pytest
  - hard set rerun
  - existing scorer rerun
- kill criteria:
  - 若实现需要第二 authority source 或 parallel mainline，则当前 milestone 失败
- files / areas likely touched:
  - `OpenEmotion/openemotion/proto_self/trial1_shadow.py`
  - `EgoCore/tests/test_trial1_shadow_replay_minimal.py`
  - `OpenEmotion/openemotion/proto_self/tests/test_trial1_shadow_contract.py`
  - `scripts/codex/evaluate_trial2_public_driver_hypotheses.py`
- acceptance:
  - 只实现两个 split ablations
  - 现有 hard set / scorer 可直接消费输出
  - 生成 Trial-2 raw/scored/decision artifacts
- validation:
  - `python3 -m py_compile ...`
  - 定向 pytest
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 若 rerun 结果不具判别性，则不扩大 suite，直接交给 M4 收口
- milestone end:
  - `continue`

### M4: Decision

- type: decision
- question:
  - 当前 bounded task 是否已经识别出 active public driver，还是该 demote / close
- current framing:
  - `bounded decision under unchanged scorer + hard set`
- hypotheses:
  - H1/H2/H3 中仅允许保留一个 “current bounded active driver” 结论
- scope:
  - 产出最终 decision
  - 不升级 repo-level state
- experiments planned:
  - decision artifact synthesis
- kill criteria:
  - 若必须引入 challenger scoring 或新 hard set 才能解释结果，则直接 `close`
- files / areas likely touched:
  - `docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2/*`
  - `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_*`
- acceptance:
  - 最终只能是：
    - `continue`
    - `demote`
    - `close`
  - 明确写出为何不是另外两个
- validation:
  - `python3 scripts/codex/verify_repo.py --mode full`
- rollback note:
  - full gate 若有 unrelated repo failure，保留本 slice 结论并显式降级口径
- milestone end:
  - `close`

## Progress

- current_status: `m4_closed_h1_identified`
- current_milestone: `M4: Decision`
- milestone_state: `completed`
- candidate_vs_proof: `proof_passed`

## Decision log

- 2026-04-09:
  - `Trial-1` 已收口为子 claim 降级
  - `Trial-2` 不再以“修复 counterfactual_writeback”为目标
  - 当前主问题改写为“识别 MVS 的真实 public causal driver”
  - `Trial-2` 明确绑定为 `M0 -> M4` 的 bounded long-run，不允许扩大候选集或改 scorer/hard set
  - `M0` 已完成并以 `continue` 收口：候选集锁定为 `H1/H2/H3`，`reflection loop` 不单列
  - `M1` 已完成并以 `continue` 收口：在当前 hard set 上，H1 `counterfactual low-success guard` 排名第 1；H2/H3 仍保留，但当前只算 latent candidates
  - `M2` 已完成并以 `continue` 收口：split-sever 判别实验、artifact 路径、decision rule 已预注册
  - `M3` 最小实现切片已落地待验证：新增 `trial2_ablation_correction_public_path_sever`、`trial2_ablation_viability_public_path_sever`、定向 fidelity tests、以及 Trial-2 decision evaluator
  - `M3` 首轮验证已通过：`py_compile`、contract pytest、replay minimal pytest 全部通过，下一步只剩 hard set rerun + scoring
  - `M3` raw rerun 已完成：`TRIAL2_PUBLIC_DRIVER_RERUN_CURRENT.json/.md` 已生成
  - `M3` scoring 已完成：`TRIAL2_PUBLIC_DRIVER_RERUN_SCORED_CURRENT.json/.md` 与 causal table 已生成；下一步只剩 decision synthesis
  - `M3` decision synthesis 首次失败：当前 scorer 只把官方 ablations 写进 `ablation_separation.by_ablation`，未自动纳入 Trial-2 split ablations；需要最小 scorer extensibility fix，但 ontology 不变
  - `M3` blocker fix 已落地：`score_trial1_shadow_replay.py` 现在会对所有 ablation variants 计算 separation，不再只看 `trial1_ablation_*`
  - `M3` decision synthesis 第二次仍失败：raw/scored artifact 里仍缺 Trial-2 split ablation entries，下一步要核对 rerun 变体接线，而不是改 ontology 或扩 suite
  - `M3` 接线核对已完成：raw / scored artifact 都包含 Trial-2 split ablations；第二次失败是并行执行时 evaluator 读到了旧 scored 文件，下一步顺序重跑 decision evaluator
  - `M3` 第三次诊断发现真正实现 bug：`trial2_ablation_*` 没接入 `trial1_variant_uses_counterfactual_public_path()`，导致 split ablations 误切 H1 path；下一步只修这个 helper，不改试验设计
  - `M3` helper wiring bug 已修复，并补了 counterfactual-preservation regression test；下一步只重跑受影响的最小验证与 Trial-2 artifacts
  - `M3` helper fix validation 已通过：`py_compile` + replay minimal pytest 通过，下一步重跑 Trial-2 raw/scored/decision artifacts
  - `M3` fixed-helper raw rerun 已完成：等待新的 scored / decision artifact
  - `M3` fixed-helper scoring 已完成：等待最终 decision artifact
  - `M3` 以 `continue` 收口：修复 wiring 后，只有 H1 sever 保留 non-zero public gap，H2/H3 sever 都近似 candidate
  - `M4` 以 `close` 收口：在 frozen scorer + hard set 下，`H1 counterfactual low-success guard` 被识别为当前 bounded active public driver

## Surprises / discoveries

- 新发现 1
  - `counterfactual_writeback` 对 `public_path_sever` 有 public signal，但不足以撑过 strongest-ablation rule
- 新发现 2
  - `alternative_explanation_isolation` 与 candidate 持平，比单纯的 counterfactual rescue 更值得成为下轮主问题
- 新发现 3
  - 当前 hard set 预载的 `recent_correction_tags` 与 `viability_pressure` 大多低于 public gate 阈值，所以 `reflection family` 不是当前 bounded task 的独立候选
- 新发现 4
  - 当前 hard set 的 `counterfactual < 0.35` 命中 `8/10` cases，而 `correction >= 0.6` 与 `viability >= 0.5` 都是 `0/10`；因此当前 scorer 面上唯一被预激活的 public gate 是 H1
- 新发现 5
  - Trial-2 的 split-sever 初版失败并不是 hard set underdefined，而是 helper wiring bug；修复后，H2/H3 的 public gap 都回到 `0.0`
- 已排除路线 1
  - 继续把 `Trial-2` 命名或 framing 成 `fix counterfactual_writeback`
- 已排除路线 2
  - 在未识别 public driver 前就推进新的 prototype logic
- 已排除路线 3
  - 把 `reflection loop` 单独升成第 4 条候选，从而突破 `<= 3` 的 stop rule

## Outcomes / retrospective

- 本轮已证明：
  - `Trial-2` 需要是一个新的 bounded public-driver task，而不是 `Trial-1` 的补丁尾声
  - `M0` 已冻结 hard constraints / stop rules / `<= 3` 候选集
  - `M1` 已给出 bounded ranking：`H1 > H2 > H3`
  - `M2` 已冻结最小判别实验：`counterfactual sever + correction-only sever + viability-only sever`
  - `M3/M4` 已在 frozen scorer + hard set 下识别出：
    - `H1 counterfactual low-success guard = current bounded active public driver`
    - `H2/H3 = not active on this bounded setup`
- 还没证明：
  - H1 是通用 MVS causal core
  - H1 在别的 replay sets / runtime slices 上也成立
- 本轮排除了什么：
  - 继续围绕旧 subclaim 做默认主线
  - 候选集扩成 `3` 条以上
- 下一步最小闭环动作：
  - `Trial-2` 已关闭；若后续继续，只能新开任务去测试 H1 是否能跨 hard set 或 replay corpus 迁移
