# MVS H1 External Replay Execution - EXPLORE

> 本任务以 implementation 为主，但保留最小实验日志，用于记录 runner 设计的关键证伪点。

## Exploration mode

- enabled: yes
- why exploration mode is needed: 需要先证实 isolated runtime + public-output ontology 能覆盖 external replay cases
- current framing: frozen case -> bounded replay plan -> isolated baseline/candidate execution -> public/mechanism summaries
- success looks like: 60-case execution complete with explicit proof ceiling
- disallowed premature claims:
  - external replay = runtime efficacy
  - H1 已在 external corpus 上证明有效

## Question reformulation

- original question: 如何在 frozen external corpus 上跑 MVS/H1
- normalized question: 如何在不改 mainline 的前提下，对 frozen cases 跑可重复的 bounded replay analysis
- why this framing is better: 它把任务收紧为 execution+analysis，而不是新机制开发

## Hypotheses

### Hypothesis 1

- statement: isolated runtime 可以消费全部 held-out cases，而不污染 canonical stores
- why plausible: runtime 和 writeback stores 都可重定向到 temp roots
- kill criteria: 必须触碰 canonical stores 才能执行
- smallest experiment: 先 probe 4 个 family

### Hypothesis 2

- statement: candidate 的 `shadow_h1` 只会在 direct synthetic exec-result buckets 上出现
- why plausible: canonical H1 patch 本来就是 observable exec-result shadow-only path
- kill criteria: negative bucket 也稳定出现 H1，或 direct bucket 不出现
- smallest experiment: correction + tool_risk probes

## Experiment log

### Cycle 01

- question: isolated runtime 是否可行
- framing used: temp-root runtime probe
- experiment: correction / continuity / ask uncertainty / tool ambiguity 小样本 probe
- command / script / artifact: ad-hoc `RuntimeV2ProtoSelfRuntime` probe
- observed result: baseline/candidate 都能执行，且未写入 canonical stores
- what it proves: external replay runner 可以建立在 isolated temp stores 上
- what it does not prove: full 60-case execution 一定无失败
- what path is ruled out: 直接用 canonical stores 跑 replay
- decision for next step: 写 full execution runner

### Cycle 02

- question: H1 shadow path 在 external replay 上的最小可观测性
- framing used: synthetic exec-result direct buckets
- experiment: correction + tool risk buckets 上插入 bounded synthetic exec-result
- command / script / artifact: ad-hoc candidate probe
- observed result: candidate 在 exec-result 后出现 `shadow_h1`，ingress-only buckets不出现
- what it proves: direct synthetic exec-result buckets 可以承载 H1 mechanism observation
- what it does not prove: public efficacy 或 runtime efficacy
- what path is ruled out: 需要 live decision wiring 才能观察 H1
- decision for next step: full held-out execution + proof ceiling

## Candidate vs proof

- candidate_found: bounded external replay runner design
- proof_pending: full held-out execution reports
- proof_passed:
- remaining proof gap: execution completeness、bucket summaries、E2/E3 claim ceiling
