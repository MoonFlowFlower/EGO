# Trial-2 Public-Driver-First Spec - EXPLORE

> 仅在 research / verify / observation / proof / high-unknown 任务中强制使用。
> 每次实验后必须先更新本文件，再开始下一轮。

## Exploration mode

- enabled: yes
- why exploration mode is needed:
  - 当前真正的问题不是“实现更多逻辑”，而是“现有 scorer + 现有 hard set 到底在点亮哪条 public causal path”
- current framing:
  - `identify the bounded active public driver for current MVS`
- success looks like:
  - 在不改 scorer ontology 和不扩 hard set 的前提下，识别一条当前 active public driver，或严格关闭任务
- disallowed premature claims:
  - `Trial-2 已识别通用 driver`
  - `counterfactual_writeback 已被完全救回`
  - `MVS 已在真实主链生效`

## Question reformulation

- original question:
  - `Trial-1` 降级后，下一步是不是要继续修 `counterfactual_writeback`
- normalized question:
  - 不继续救旧理论，而是先识别当前 hard set / scorer 真正点亮了哪条 public path
- why this framing is better:
  - 它直接对准当前 scorer 能看的信号面
  - 它符合 bounded long-run 的 stop rule
  - 它允许把 `counterfactual_writeback`、`correction-pressure`、`viability-pressure` 放在同一 public surface 上比较

## Hypotheses

### Hypothesis 1

- statement:
  - H1 `counterfactual low-success guard` 是当前 bounded hard set 上的 active public driver
- why plausible:
  - 既有 rerun 中，candidate 只对 `counterfactual_public_path_sever` 产生 public gap
  - 现有 hard set 预载的 `counterfactual_success_by_action` 在 positive cases 中稳定低于 `< 0.35`
- kill criteria:
  - 若 split rerun 显示 correction-only 或 viability-only sever 也产生同级 public gap，则 H1 降级
- smallest experiment:
  - 保持 hard set / scorer 不变，新增 correction-only 和 viability-only split sever

### Hypothesis 2

- statement:
  - H2 `correction-pressure public guard` 是当前 bounded hard set 上的 backup driver
- why plausible:
  - hard set 中多数 cases 至少预载了非零 `recent_correction_tags`
- kill criteria:
  - 若 split rerun 中 correction-only sever 对 public outputs 仍为 `~0` gap，则 H2 降级
- smallest experiment:
  - 只切 correction public path，保持 counterfactual / viability path 不变

### Hypothesis 3

- statement:
  - H3 `viability-pressure public guard` 是当前 bounded hard set 上的 tertiary driver
- why plausible:
  - 现有 policy surface 确实有 viability-driven `ask_preferred / risk_bias` path
- kill criteria:
  - 若 split rerun 中 viability-only sever 对 public outputs 仍为 `~0` gap，则 H3 降级
- smallest experiment:
  - 只切 viability public path，保持 counterfactual / correction path 不变

## Rejects

- reject 1:
  - `reflection loop` 作为 standalone public-driver hypothesis
  - reason:
    - 当前 hard set 是 ingress-only preload diagnostic，不足以把 reflection loop 独立从 H2/H3 中分离出来
- reject 2:
  - `fix counterfactual_writeback`
  - reason:
    - 这是旧子 claim 的沉没成本 framing，不是 Trial-2 的 bounded objective
- reject 3:
  - `combined correction + viability + reflection family` 作为单一候选
  - reason:
    - 这会直接破坏 `<= 3` 候选约束，也无法在当前 hard set 上做最小区分

## Experiment log

### Cycle 01

- question:
  - `Trial-1` 子 claim 已降级后，新的长任务应该对准什么问题
- framing used:
  - `public-driver-first`
- experiment:
  - 用 `Trial-1` closeout 结果反推 Trial-2 的问题表述和非目标
- command / script / artifact:
  - `docs/codex/tasks/ai-self-awareness-minimal-framework/STATUS.md`
  - `artifacts/self_awareness_research/TRIAL1_REDESIGNED_ABLATION_EVALUATION_CURRENT.json`
  - `python3 scripts/codex/new_task.py identify-public-causal-driver-for-mvs-trial-2 --title "Trial-2 Public-Driver-First Spec"`
- observed result:
  - `Trial-2` 已独立建档
  - 当前 framing 明确从“救旧 subclaim”切到“识别 public causal driver”
- what it proves:
  - 新任务不必继续被 `counterfactual_writeback` 沉没成本绑架
- what it does not prove:
  - 当前主导 public driver 已经被识别
- what path is ruled out:
  - `fix counterfactual_writeback` 作为任务名或默认目标
- decision for next step:
  - 冻结 `<= 3` hypotheses，并只保留当前 scorer/hard set 可区分的路径

### Cycle 02

- question:
  - bounded Trial-2 的问题、stop rule、和候选集应该如何冻结
- framing used:
  - `M0 problem freeze before implementation`
- experiment:
  - 把 Trial-2 重写成 `M0 -> M4` bounded long-run，并显式压缩为 `H1/H2/H3`
- command / script / artifact:
  - `docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2/PLAN.md`
  - `docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2/STATUS.md`
  - `git diff --check -- docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2`
- observed result:
  - `M0` 完成
  - `reflection loop` 不再作为 standalone hypothesis
  - `M0` terminal label = `continue`
- what it proves:
  - 当前任务不会在实现阶段再扩大候选集或改变问题定义
- what it does not prove:
  - H1/H2/H3 的排序和 active driver 结论
- what path is ruled out:
  - `>3` 候选
  - `reflection-only` 独立候选
- decision for next step:
  - 进入 `M1`，用既有 Trial-1 artifacts 给出 bounded ranking

### Cycle 03

- question:
  - 在当前 hard set / scorer 下，H1/H2/H3 应该如何排名
- framing used:
  - `bounded ranking from current trigger reachability`
- experiment:
  - 统计现有 hard set 里各 public gate 的预载触发命中，并对照既有 Trial-1 rerun 的 ablation gaps
- command / script / artifact:
  - `docs/codex/tasks/ai-self-awareness-minimal-framework/TRIAL1_COUNTERFACTUAL_HARD_SET.json`
  - `artifacts/self_awareness_research/TRIAL1_HARD_SET_RERUN_SCORED_CURRENT.json`
  - `artifacts/self_awareness_research/TRIAL1_HARD_SET_CAUSAL_SEPARATION_CURRENT.json`
- observed result:
  - `counterfactual < 0.35` 命中 `8/10` cases
  - `correction >= 0.6` 命中 `0/10` cases
  - `viability >= 0.5` 命中 `0/10` cases
  - candidate 只对 `trial1_ablation_counterfactual_public_path_sever` 产生 non-zero public gap
- what it proves:
  - 在当前 bounded setup 上，H1 是最强 mainline hypothesis
  - H2/H3 当前更像 latent candidates，不是 active public driver
- what it does not prove:
  - H1 是通用 driver
  - H2/H3 在别的 hard set 上也无效
- what path is ruled out:
  - 把 `reflection family` 或 `combined family` 升成新候选
- decision for next step:
  - 进入 `M2`，把判别实验冻结成 `counterfactual sever + correction-only sever + viability-only sever`

### Cycle 04

- question:
  - 在不改 scorer / hard set 的前提下，最小判别实验应该长什么样
- framing used:
  - `split-sever only the public path under test`
- experiment:
  - 预注册 rerun 变体集、artifact 输出路径、decision rule
- command / script / artifact:
  - `docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2/TRIAL2_DISCRIMINATIVE_EXPERIMENT_SPEC.md`
  - `git diff --check -- docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2`
- observed result:
  - 判别实验固定为 `baseline + candidate + 3 sever ablations`
  - scorer ontology 仍不变
  - hard set 仍不变
  - `M2` terminal label = `continue`
- what it proves:
  - 接下来的实现不会因为中途解释困难而偷偷换 scorer 或换 case set
- what it does not prove:
  - 哪条 hypothesis 最终胜出
- what path is ruled out:
  - 用新的 replay cases 或新的 scorer 语义来“帮忙”找 driver
- decision for next step:
  - 进入 `M3`，只实现 `correction-only sever` 和 `viability-only sever`

### Cycle 05

- question:
  - split-sever 首次 rerun 为什么没有给出判别结果
- framing used:
  - `debug the bounded experiment before changing the experiment`
- experiment:
  - 对比 raw/scored artifact 与 helper wiring，确认是 hard set underdefined 还是 implementation bug
- command / script / artifact:
  - `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_RERUN_CURRENT.json`
  - `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_RERUN_SCORED_CURRENT.json`
  - `PYTHONPATH=OpenEmotion python3 - <<'PY' ... inspect trial1_variant_uses_*_public_path helpers ... PY`
- observed result:
  - `trial2_ablation_*` 最初没有保留 counterfactual public path
  - split-sever 首次失败来自 helper wiring bug，而不是任务 underdefined
- what it proves:
  - 当前任务仍可在原范围内闭环，不需要扩 hard set 或 scorer
- what it does not prove:
  - H1 已经被识别
- what path is ruled out:
  - 因首次失败就直接宣称 “current hard set underdefined”
- decision for next step:
  - 只修 helper wiring，并补 preservation regression

### Cycle 06

- question:
  - 修复 wiring 后，frozen rerun 是否能识别唯一 active public driver
- framing used:
  - `same hard set, same scorer, fixed helper`
- experiment:
  - 重跑 raw rerun -> scorer -> decision evaluator
- command / script / artifact:
  - `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_RERUN_CURRENT.json`
  - `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_RERUN_SCORED_CURRENT.json`
  - `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_DECISION_CURRENT.json`
- observed result:
  - H1 sever:
    - `mean_weighted_gap = 0.05`
    - `positive_gap_case_count = 8`
  - H2 sever:
    - `mean_weighted_gap = 0.0`
    - `positive_gap_case_count = 0`
  - H3 sever:
    - `mean_weighted_gap = 0.0`
    - `positive_gap_case_count = 0`
- what it proves:
  - 在 frozen scorer + hard set 下，H1 是当前 bounded active public driver
- what it does not prove:
  - H1 是通用 causal core
  - H1 在 runtime 或别的 replay set 也成立
- what path is ruled out:
  - H2/H3 作为当前 bounded setup 的 active public-driver explanations
- decision for next step:
  - `M4 = close`

### Cycle 07

- question:
  - closeout 时应如何表述验证口径
- framing used:
  - `slice-complete, repo-full-not-clean`
- experiment:
  - scoped diff check + `verify_repo --mode fast` + `verify_repo --mode full`
- command / script / artifact:
  - `git diff --check -- ...Trial-2 slice...`
  - `python3 scripts/codex/verify_repo.py --mode fast`
  - `python3 scripts/codex/verify_repo.py --mode full`
- observed result:
  - scoped diff check = pass
  - fast gate = pass
  - full gate 暴露全仓历史失败，不属于 Trial-2 定向 slice
- what it proves:
  - Trial-2 这条 bounded slice 已经闭环
- what it does not prove:
  - repo full gate clean
- what path is ruled out:
  - 把 repo-level full-gate 失败误写成 Trial-2 实现回归
- decision for next step:
  - `Trial-2 closed`

## Framing changes

- 2026-04-09:
  - `repair Trial-1 counterfactual claim` -> `identify bounded active public driver for current MVS`
  - 理由：避免继续优化已降级的旧子机制，并服从 `<= 3` 候选与 `no scorer/hard-set changes` 的 stop rule

## Candidate vs proof

- candidate_found:
  - H1 `counterfactual low-success guard`
  - H2 `correction-pressure public guard`
  - H3 `viability-pressure public guard`
- proof_pending:
  - bounded ranking
  - split-sever diagnostic rerun
- proof_passed:
  - none
- remaining proof gap:
  - 还没有 Trial-2 自己的 split-sever rerun 和 decision artifact
