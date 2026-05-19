# Exploration Plans

> `PLAN.md` 是 harness 级总计划。
> `PLANS.md` 是本轮 operational research program 的逐探索账本。

## Program state

- phase: `Phase 1`
- framing_status: `reframed`
- current_exploration: `E10 (completed)`
- consecutive_non_shrinking_failures: `0`
- stopping_rule:
  - 若连续 `3` 个 explorations 失败且没有缩小不确定性，则停止并重构 framing

## Core rules

- 每个 exploration 只测试 `1` 个 falsifiable hypothesis
- 每次实验、test run、或代码改动后，先更新本文件和 `STATUS.md`
- 优先运行最小可杀实验
- 若 eval 不可靠，先修 eval，不扩 implementation

## Exploration queue

### E00

- status: `completed`
- hypothesis:
  - `Anthropomorphic narrative shell does not meaningfully improve the 5 operational targets over baseline chat under held-out tests.`
- why this matters:
  - 先杀掉最容易把任务带偏的坏路线
- smallest test:
  - `baseline_chat` vs `narrative_identity_shell`
- kill target:
  - 若 narrative 只提高 wording、不提高 target scores，则 reject
- expected uncertainty reduction:
  - 把“像自我”与“会变行为”分开

### E01

- status: `completed`
- hypothesis:
  - `Operational self-loop core is sufficient to produce measurable improvement on all 5 operational targets over baseline and single-axis partial candidates.`
- why this matters:
  - 这是当前主线候选的第一道生死门
- smallest test:
  - `baseline_chat` / `identity_only` / `trace_only` / `operational_self_loop_core`
- kill target:
  - 若 operational core 不能同时过 `T1-T5`，则 mainline 候选失败
- expected uncertainty reduction:
  - 回答“最小 core 是否存在”

### E02

- status: `completed`
- hypothesis:
  - `Operational self-loop core has a better build-now tradeoff than larger alternatives, even if some larger candidates score slightly higher in raw performance.`
- why this matters:
  - 用户要的是 smallest implementable mechanism，不是 raw max architecture
- smallest test:
  - `operational_self_loop_core` vs `mvs_aligned_compact` vs `active_inference_self_model`
- kill target:
  - 若更大候选在依赖成本可接受的前提下明显压过 mainline，则切换主线
- expected uncertainty reduction:
  - 回答“build now 该选谁”

### E03

- status: `completed`
- hypothesis:
  - `MVS-aligned compact remains the first build-first choice under at least 5 seeds, 3 held-out splits, and score-weight perturbations of ±10% to ±20%.`
- why this matters:
  - 当前 held-out eval 只给了单次排序，还不能支撑稳定主线选择
- smallest test:
  - 固定 candidate set，不改机制，只重跑 ranking robustness audit
- kill target:
  - 若 `MVS-aligned compact` 的 win rate 不足、rank variance 明显更差、或对权重扰动过敏，则它不能继续作为当前主线
- expected uncertainty reduction:
  - 回答“当前主线是稳健第一，还是只是单次 eval 里的偶然赢家”

### E04

- status: `completed`
- hypothesis:
  - `MVS-aligned compact can be specified as a minimal extension of the current OpenEmotion proto_self formal mainline without introducing a new authority surface.`
- why this matters:
  - 若 prototype design 只能靠另开 state owner 或另起 runtime 旁路表达，那这个主线不值得实现
- smallest test:
  - 用现有 `proto_self` state / kernel / reducer / trace contract 写 formal prototype design
- kill target:
  - 若关键机制无法落在现有正式接口：
    - `IdentityInvariants`
    - `SelfModel`
    - `DriveField`
    - `CycleStore`
    - `EpisodicTrace`
    - `KernelOutput`
    则当前主线失败
- expected uncertainty reduction:
  - 回答“这条主线能否在不破坏 single-authority 的前提下实现”

### E05

- status: `completed`
- hypothesis:
  - `A replay validator can distinguish baseline, MVS, ablations, and active-inference with explicit pass/fail and challenger-switch rules before any prototype code exists.`
- why this matters:
  - 如果还没有 validator，就没有资格继续做实现
- smallest test:
  - 先写 replay validator spec，不写运行时代码
- kill target:
  - 若无法定义清晰的 held-out replay thresholds，当前 program 只能停留在 synthetic ranking，不能进入实现
- expected uncertainty reduction:
  - 回答“后续 prototype 到底怎么被杀、怎么被保留、何时切到 challenger”

### E06

- status: `completed`
- hypothesis:
  - `A shadow-only Trial-1 replay slice can be run on the formal adapter/runtime builder path without creating a second authority source or changing default behavior when the feature flag is off.`
- why this matters:
  - 这是从设计进入最小实现的 admission gate；如果这一步都要绕开 formal path，当前主线就不值得继续
- smallest test:
  - 冻结 replay corpus manifest
  - 加 leakage guard
  - 定义 runner contract IDs
  - 用最小 MVS slice 跑一个 shadow-only replay trial
- kill target:
  - 若必须新建 owner、绕开 adapter、或默认行为在 flag-off 时漂移，则 kill
- expected uncertainty reduction:
  - 回答“当前主线能否先以最小 shadow slice 进入 replay trial，而不是继续停留在 paper design”

### E07

- status: `completed`
- hypothesis:
  - `The current Trial-1 shadow replay artifact can be scored with a representation-neutral ontology that yields admission_passed and decision_adjacent_passed, but not replay_efficacy_passed.`
- why this matters:
  - 如果 scorer 仍依赖 MVS 私有字段或无法复用到 challenger，当前 replay artifact 还不能进入正式 validator 主链
- smallest test:
  - 冻结 scorer ontology、weights、negative-control penalties、ablation separation rules
  - 对现有 `TRIAL1_SHADOW_REPLAY_CURRENT.json` 打分
- kill target:
  - 若 scorer 无法在不改 ontology 的情况下未来评 `active-inference` challenger，则该 scoring slice 失败
- expected uncertainty reduction:
  - 回答“当前 Trial-1 artifact 到底只过了 admission，还是已经有 decision-adjacent / replay-efficacy 证据”
- result:
  - scorer ontology 已冻结为 public-output-only contract，不读取 MVS 私有 state / shadow fields
  - `trial1_candidate_mvs_aligned_compact` 当前结果：
    - `admission_passed = true`
    - `decision_adjacent_passed = true`
    - `replay_efficacy_passed = false`
  - negative controls clean，stability penalty = `0.0`
  - replay efficacy 当前被 ablation separation 卡住：
    - `trial1_ablation_minus_counterfactual_writeback` 与 candidate 持平
    - `minimum_mean_weighted_gap_vs_ablations = 0.0`
- decision:
  - 当前 scorer 可复用到未来 challenger，对 `active-inference self-model` 不需要改 scoring ontology
  - 当前不推进 replay suite 扩容，也不新增 prototype 逻辑
  - task-doc closeout 后已补跑：
    - scoped `git diff --check`
    - `python3 scripts/codex/verify_repo.py --mode fast`
    - 两者都通过
  - 最终 closeout rerun 再次确认：
    - scoped `git diff --check`
    - `python3 scripts/codex/verify_repo.py --mode fast`
    - 两者都通过

### E08

- status: `completed`
- hypothesis:
  - `The current strongest ablation tie is caused by a mis-specified counterfactual_writeback ablation on the representation-neutral scorer surface, not by evidence that counterfactual_writeback has no causal value.`
- why this matters:
  - 在 candidate 没有 beat strongest ablation 之前，不能去做 challenger 比较，也不能继续把当前 counterfactual claim 写得更强
- smallest test:
  - 审计当前 raw replay artifact
  - 比较：
    - candidate vs strongest ablation
    - candidate vs neighboring viability ablation
  - 再给出一个 diagnostic-only hard set
- kill target:
  - 若 strongest ablation tie 无法在 representation-neutral ontology 下被解释，则这条 causal-gap diagnosis 失败
- expected uncertainty reduction:
  - 回答“现在该扩 suite、重设 ablation，还是直接降级机制宣称”
- result:
  - candidate vs strongest ablation：
    - `0` gap cases
    - `0` public-gap steps
    - `4` private-only cases
    - `9` private-only steps
  - candidate vs neighboring viability ablation：
    - `4` gap cases
    - `9` public-gap steps
  - reachability audit 显示：
    - failure/blocked 会同时写入 low prediction 与 correction tags
    - success-after-correction 又会把 prediction 拉回 `>= 0.65`
    - 因而 current Trial-1 path 上没有自然暴露出的 counterfactual-only public phase
- decision:
  - final decision = `redesign_ablation`
  - 当前不扩 official replay suite
  - 当前不评分 `active-inference`
  - 当前 narrow mechanism claim 降级为 `unproven under current ontology`
  - closeout validation：
    - `git diff --check -- ...Trial-1 causal-gap slice...` 通过
    - `python3 scripts/codex/verify_repo.py --mode fast` 通过

### E09

- status: `completed`
- hypothesis:
  - `The strongest ablation should be redesigned around public-path causal faithfulness, and a second ablation is needed to isolate alternative public-path explanations without changing the scorer ontology.`
- why this matters:
  - 如果 redesign spec 还是围绕 private-state deletion，就会再次得到一个对 scorer 不可见、但看起来像“强对照”的假 ablation
- smallest test:
  - 基于 current causal-gap diagnosis 产出 doc-only redesign spec
- kill target:
  - 若 spec 的设计目标变成“帮助 candidate 赢”，而不是忠实切断 causal path，则该切片失败
- expected uncertainty reduction:
  - 回答“下一次最小 rerun 应该跑哪两个 ablations，以及看到什么结果才该降级 claim”
- result:
  - 已定义两个 redesigned ablations：
    - `trial1_ablation_counterfactual_public_path_sever`
    - `trial1_ablation_alternative_explanation_isolation`
  - 已明确：
    - 每个 ablation 要切断的 causal path
    - 预期应变化的 public outputs
    - 必须保持稳定的非目标行为
    - 何种结果会 demote `counterfactual_writeback` claim
  - 已冻结 minimal rerun plan：
    - 只在既有 hard set 上跑 baseline / candidate / 2 redesigned ablations
    - 不扩 official replay suite
    - 不比 challenger
- decision:
  - 当前下一步不是扩 replay，也不是 challenger compare，而是实现 redesigned ablations 并只在 hard set 上 rerun
  - closeout validation：
    - `git diff --check -- ...Trial-1 ablation-redesign spec slice...` 通过
    - `python3 scripts/codex/verify_repo.py --mode fast` 通过

### E10

- status: `completed`
- hypothesis:
  - `If counterfactual_writeback has real public-path causal value, the candidate will beat the redesigned public-path-sever ablation on the existing hard set under the unchanged representation-neutral scorer.`
- why this matters:
  - 在 candidate 没有 beat redesigned strongest ablation 之前，不能继续保留更强的 counterfactual_writeback claim，也不能推进 challenger compare
- smallest test:
  - 冻结 fidelity checks / outcome interpretation / gap thresholds
  - 只实现：
    - `trial1_ablation_counterfactual_public_path_sever`
    - `trial1_ablation_alternative_explanation_isolation`
  - 只在既有 hard set 上 rerun baseline / candidate / 2 redesigned ablations
- kill target:
  - 若 candidate 仍无法在 public representation-neutral outputs 上 beat redesigned strongest ablation，则 demote claim
- expected uncertainty reduction:
  - 回答“当前 strongest ablation tie 是 mis-spec 被修正后会消失，还是 counterfactual_writeback claim 本来就过强”
- result:
  - prereg 已冻结：
    - `TRIAL1_ABLATION_FIDELITY_CHECKS.md`
    - `TRIAL1_OUTCOME_INTERPRETATION_MATRIX.md`
    - `TRIAL1_GAP_THRESHOLDS.md`
  - fidelity checks 已通过：
    - official contract 仍冻结
    - `public_path_sever` 只切断 counterfactual public path
    - `alternative_explanation_isolation` 只切断 correction / viability public paths
  - hard-set rerun 结果：
    - candidate weighted support = `0.05`
    - `trial1_ablation_counterfactual_public_path_sever` weighted support = `0.0`
    - `trial1_ablation_alternative_explanation_isolation` weighted support = `0.05`
  - candidate vs `trial1_ablation_counterfactual_public_path_sever`：
    - `8/8` positive cases 都出现 public gap
    - 但 `mean_weighted_gap = 0.05`，未达到冻结阈值 `0.10`
    - relation = `indeterminate`
  - candidate vs `trial1_ablation_alternative_explanation_isolation`：
    - `mean_weighted_gap = 0.0`
    - `public_gap_case_rate = 0.0`
    - relation = `candidate_approx_ablation`
  - redesigned strongest ablation 依 frozen rule 选为：
    - `trial1_ablation_alternative_explanation_isolation`
- decision:
  - final decision = `demote_current_claim`
  - 当前不能再写：
    - `counterfactual_writeback replay-efficacy contributor provisionally survives`
  - 当前更窄的允许口径是：
    - `counterfactual_writeback creates policy-surface separation against the public-path-sever ablation on the hard set, but fails the frozen strongest-ablation rule`
  - 当前不扩 replay suite
  - 当前不做 challenger scoring
  - 当前不升级 repo-level state

## Decision log

- 2026-04-09:
  - 当前问题正式从“AI 自我意识”重构为“operational self-governance mechanism”
  - `mainline candidate` 先设为 `operational self-loop core`
  - `backup candidate` 先设为 `MVS-aligned compact`
  - `active-inference self-model` 降为 `reject for now as build-now mainline`
- 2026-04-09:
  - 已新增 `scripts/codex/run_operational_self_model_evals.py`
  - validator 先于实现扩展落地
  - 下一步只允许跑 `E00 -> E01 -> E02`
- 2026-04-09:
  - `python3 -m py_compile scripts/codex/run_operational_self_model_evals.py` 已通过
  - 现在进入第一次 held-out operational eval
- 2026-04-09:
  - `python3 scripts/codex/run_operational_self_model_evals.py` 首轮结果：
    - `E00` pass，narrative shell 被杀掉
    - `E01` fail，`operational_self_loop_core` 没有通过 `T1-T5`
    - `E02` fail，当前 build-now tradeoff 更好的是 `MVS-aligned compact`
  - 当前 uncertainty 明显缩小：
    - “5 组件最小 core 是否足够” -> 当前答案是否
    - “是否还需要 MVS 级结构” -> 当前答案是需要
- 2026-04-09:
  - 发现 harness summary 仍写死旧 mainline，已修正为：
    - 选择最小过线候选为 `mainline`
    - 选择下一名过线候选为 `backup`
  - 现在重跑 held-out eval 以做正式 candidate selection
- 2026-04-09:
  - 重跑后正式收敛：
    - `mainline candidate = MVS-aligned compact`
    - `backup candidate = active-inference self-model`
    - `operational self-loop core = reject`
  - 当前 program recommendation：
    - `build now`
- 2026-04-09:
  - fast gate 抓到 `OPERATIONAL_TARGETS.md:5` trailing whitespace
  - 已立即修复；下一步重跑 fast gate
- 2026-04-09:
  - independent reviewer 抓到 `STATUS.md` 中 “mainline 已选定” 与 “mainline 仍 provisional” 的冲突
  - 已修复该矛盾，并同步 fast-gate pass 结果
- 2026-04-09:
  - 根据当前用户约束，之前的 `build now` 口径全部降级为：
    - `current best build-first candidate under current eval setup`
  - 新的主问题变成：
    - `MVS-aligned compact` 是否是稳健第一
    - 若不是，何时切到 `active-inference self-model`
  - 下一步只允许推进：
    - `E03` ranking robustness audit
    - `E04` prototype design
    - `E05` replay validator spec
- 2026-04-09:
  - 已新增 `scripts/codex/run_operational_selection_robustness.py`
  - 该脚本只做：
    - `>= 5` seeds
    - `>= 3` held-out splits
    - `±10%` 到 `±20%` weight perturbations
  - `python3 -m py_compile scripts/codex/run_operational_selection_robustness.py` 已通过
  - 首次运行失败：
    - 动态导入 `run_operational_self_model_evals.py` 时未注册 `sys.modules`
    - dataclass 初始化报错
  - 已修复：
    - 在 robustness 脚本的动态导入路径上显式注册 `sys.modules[spec.name]`
  - 最终 audit 已无警告通过，当前结论：
    - `MVS-aligned compact` 在 `5 seeds x 3 splits x 35 weight scenarios = 525` 个 ranking scenarios 中 win rate `0.9867`
    - `MVS-aligned compact` baseline seed/split wins = `15/15`
    - `MVS-aligned compact` mean rank = `1.0133`
    - `MVS-aligned compact` rank variance = `0.0132`
    - `MVS-aligned compact` weight rank change rate = `0.0137`
    - `active-inference self-model` 只在 `7` 个 `process_minus_20` 场景反超
    - 当前 robust-first 结论 = `yes`
  - 发现一个非逻辑问题：
    - UTC 时间戳写法触发 deprecation warning
  - 已切到 timezone-aware 时间戳并完成无警告重跑
  - 已完成：
    - `RANKING_ROBUSTNESS_AUDIT.md`
    - `MVS_ALIGNED_COMPACT_PROTOTYPE_DESIGN.md`
    - `REPLAY_VALIDATOR_SPEC.md`
    - repo-level `PROGRAM_STATE_UNIFIED.yaml` / evidence ledger sync
  - closeout validation 已通过
- 2026-04-09:
  - 新的实现切片被约束为 `Trial-1 shadow replay`
  - 当前不允许：
    - full prototype
    - repo-level state upgrade
    - second authority source
    - parallel mainline
  - 当前只允许：
    - replay manifest
    - bucket stratification
    - leakage guard
    - runner contract
    - minimal shadow-only MVS slice
    - artifact logging
- 2026-04-09:
  - `proto_self` 最小 Trial-1 shadow slice 已落地到正式 owner path：
    - `SelfModel.counterfactual_success_by_action`
    - `SelfModel.recent_correction_tags`
    - `DriveField.viability_pressure`
    - `EpisodicRecord.corrective_trace`
  - 已补 baseline drift guard：
    - `trial1` context 存在时，只有 `candidate / ablations` 会进入最小 MVS 写回
    - `baseline` 只保留 formal path，不做 shadow 语义更新
  - Trial-1 manifest contract / leakage 校验已收回到单一 helper：
    - `openemotion.proto_self.trial1_shadow`
  - Trial-1 admission assets 已落地：
    - `TRIAL1_REPLAY_CORPUS_MANIFEST.json`
    - `scripts/codex/run_trial1_shadow_replay.py`
    - formal-path targeted tests
  - 首轮定向验证暴露两个 blocker：
    - `OpenEmotion` manifest test 的 repo root 解析偏高一层
    - `permission denied` 被归到 `blocked` 后，没有进入 failure reflection
  - blocker 修复已落地：
    - manifest test root 已对齐 repo 正根
    - `blocked` 已进入 `external_failure` correction path
  - 二轮定向验证剩余一个非逻辑问题：
    - test 仍把 `permission denied` 断言成 `failure`
    - canonical contract 下该结果应为 `blocked`
  - 测试断言已对齐 canonical `blocked` 分类
  - 三轮定向验证收口到一个 formal-path 事实：
    - `trial1` follow-up guard 已进入 `policy_hint`
    - 但 v2 上游层把最终 `preferred_mode` 压成 `defer`，而不是 v1 预期的 `ask`
  - 这说明 Trial-1 admission 应以：
    - `policy_hint.shadow_repair_bias`
    - `memory_update.corrective_trace`
    - `later guarded divergence`
    作为主验证口径，而不是死盯 `ask`
  - Trial-1 shadow replay 已实际跑出 artifacts：
    - candidate vs baseline 的有效差异集中在 `guard_shift + corrective_trace_shift`
  - replay trial 已执行，当前只差最终验证收口
  - 最终验证当前状态：
    - targeted pytest 已通过
    - scoped `git diff --check` 抓到 `appraisal.py` 两处 trailing whitespace
    - `fast` gate 仍在运行
  - trailing whitespace 已修复，等待最终 gate 重跑
  - 最终 gate 已通过：
    - scoped `git diff --check`
    - `python3 scripts/codex/verify_repo.py --mode fast`
- 2026-04-09:
  - `E07` 已完成：
    - `scripts/codex/score_trial1_shadow_replay.py` 已冻结 representation-neutral scorer
    - `TRIAL1_SHADOW_REPLAY_SCORED_CURRENT.{md,json}` 与 causal table 已产出
    - 当前 candidate 只达到：
      - `admission_passed`
      - `decision_adjacent_passed`
    - 当前 candidate 尚未达到：
      - `replay_efficacy_passed`
    - 主要 blocker 不是 negative controls，而是对 `trial1_ablation_minus_counterfactual_writeback` 缺少 separation
    - 当前 repo-level state 维持不升级，`active-inference` 继续保持 live challenger
- 2026-04-09:
  - `E08` 已完成：
    - 已新增 `TRIAL1_CAUSAL_GAP_PLAN.md`
    - 已新增 diagnostic-only hard set：`TRIAL1_COUNTERFACTUAL_HARD_SET.json`
    - 已新增 `scripts/codex/diagnose_trial1_causal_gap.py`
    - 已产出：
      - `TRIAL1_CAUSAL_SEPARATION_CURRENT.md`
      - `TRIAL1_CAUSAL_SEPARATION_CURRENT.json`
      - `TRIAL1_CAUSAL_SEPARATION_TABLE_CURRENT.md`
    - 当前正式结论不是扩 replay，也不是 challenger compare，而是：
      - `redesign_ablation`
    - 直接原因：
      - current strongest ablation tie 只剩 private-state diff
      - neighboring viability ablation 仍能被同一 scorer 看见
      - 说明 scorer 没瞎，问题在 strongest ablation 设计
- 2026-04-09:
  - `E09` 已完成：
    - 已新增 `TRIAL1_ABLATION_REDESIGN_SPEC.md`
    - 已把 strongest ablation 的 redesign 原则锁成：
      - public-path sever
      - alternative-explanation isolation
    - 当前 spec 明确拒绝：
      - private-state-only strongest ablation
      - candidate-advantage-oriented redesign

## Open uncertainties

- `identity_anchor` 是否足以在 held-out reset 条件下稳定工作
- `tension_field` 是否真的会改变行为，而不是只改变解释
- `corrective_trace` 是否能带来可测的 post-failure improvement
- `MVS-aligned compact` 是否只是在当前权重和单次 split 下获胜
- `MVS-aligned compact` 能否在现有 `OpenEmotion/proto_self` 正式状态与输出契约中自然表达
- replay validator 是否会把 `active-inference self-model` 提前升级为 challenger 主线
- Trial-1 minimal slice 是否需要新增字段，还是能完全复用现有 state classes
- replay corpus 是否足够覆盖 identity / correction / tension / restart buckets，同时完全避开 synthetic audit leakage
