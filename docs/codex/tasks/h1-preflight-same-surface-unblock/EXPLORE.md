# H1 Preflight Same-Surface Unblock - EXPLORE

> 本任务主模式是 implementation，但因涉及 preflight proof 与 causality exclusion / clear transition，保留最小探索记账。

## Exploration mode

- enabled: yes
- why exploration mode is needed: 必须证明 contamination 真正消失，而不是只看到局部测试变绿
- current framing: `native_loop` scoped blocker repair + clean-bind provenance recovery
- success looks like: `decision=continue` 的 preflight 与 causality-clear note
- disallowed premature claims:
  - `E4 sampling resumed`
  - `runtime efficacy proven`
  - `repo-level state upgraded`

## Question reformulation

- original question: 为什么 H1 E4 sampling path 还不能继续
- normalized question: 当前 frozen sampling path 是否仍被 `native_loop` / live bind 同面失败污染
- why this framing is better: 直接对准可采样前提，而不是讨论 H1 行为有效性

## Hypotheses

### Hypothesis 1

- statement: `native_loop` 当前 blocker 是 test fixture drift，不是 production semantic regression
- why plausible: `contract_runtime` 已切到 `generate_with_messages()`，而目标测试的 fake client 没跟进
- kill criteria: 修完 fixture 后失败仍落在 production path
- smallest experiment: 仅补 fake client surface，然后 rerun `test_native_loop.py`

### Hypothesis 2

- statement: temporary clean worktree + mirrored fileset 足以把 H1 slice clean-bind 到 current `HEAD`
- why plausible: 当前 contamination 主要来自 dirty root 和 stale live bind，不是 observation contract 自身失败
- kill criteria: worktree live version 仍写出 `git_dirty=true` 或 preflight 仍报 same-surface contamination
- smallest experiment: 建 worktree、镜像 fileset、启动 Telegram、重跑 preflight

## Experiment log

### Cycle 01

- question: `native_loop` blocker 是否只来自 fixture drift
- framing used: 最小修复测试 surface，不碰 runtime semantics
- experiment: 给 `EgoCore/tests/test_native_loop.py::FakeLLMClient` 增补 `generate_with_messages()`
- command / script / artifact:
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_native_loop.py EgoCore/tests/test_telegram_bot_native_switch.py -q`
- observed result: `18 passed`
- what it proves: 当前 same-surface blocker 已离开 `native_loop` scoped tests
- what it does not prove: clean-bind live process 已恢复；preflight 已 clean
- what path is ruled out: 把该失败面升级为 production contract runtime regression
- decision for next step: 构建 clean-bind automation，并在 clean worktree 上重跑 preflight

### Cycle 02

- question: clean-bind provenance 能否在 dirty canonical root 之外被最小化重建
- framing used: mirrored worktree 是 authority-neutral execution shell，不是第二 proto_self engine
- experiment: 实现 `run_h1_clean_bind_cycle.py` + causality-clear payload builder，并补 unit check
- command / script / artifact:
  - `python3 -m py_compile scripts/codex/run_h1_clean_bind_cycle.py scripts/codex/run_h1_e4_sampling_preflight.py scripts/codex/h1_e4_sampling_common.py EgoCore/tests/test_h1_e4_sampling_tools.py EgoCore/tests/test_native_loop.py`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_live_process_version.py EgoCore/tests/test_h1_e4_sampling_tools.py -q`
- observed result: tooling compile 通过；sampling helper tests `5 passed`
- what it proves: clean-bind execution path 已有最小可执行骨架与 note schema
- what it does not prove: worktree live bind 实际成功
- what path is ruled out: 在没有 clean-bind script 的情况下手工临时拼接 live provenance
- decision for next step: 运行 clean-bind cycle，拿正式 preflight `continue`

## Framing changes

- 2026-04-09: 从“继续修 H1 sampling”改成“先证明 same-surface contamination 消失”；原因是当前 blocker 在 sampling admission 之前

## Candidate vs proof

- candidate_found: `native_loop` blocker 已被 scoped fix 消除
- proof_pending: clean-bind live Telegram process + preflight `continue`
- proof_passed: no
- remaining proof gap: 还缺 causality-clear note 与 clean preflight report
