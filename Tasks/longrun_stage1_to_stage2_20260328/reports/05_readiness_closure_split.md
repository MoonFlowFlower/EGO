# Step 05 — Readiness-Closure Split

## 改了什么

- 把 `STAGE2-05` 从“直接进入 bounded repair”收正为“先做 readiness-closure split，再进入 bounded repair”。
- 明确把当前 `not_ready` 拆成两条 closure 轨道：
  - `Stage 1 strengthening blockers`
  - `readiness-evidence blockers`
- 保留 `numeric_leak` 作为第一个 bounded strengthening candidate，但不再把它写成“修完即可进入 Stage 2”的隐含前提。

## 我自 review 发现并修了什么

- 发现原先的 `next repair candidate = numeric_leak` 容易让后续执行把 `T07.3` 当成 promotion-readiness 主证据，这是权威口径漂移。
- 已按 authority source 修正：
  - `T07.3` 只证明 `Layer 2 mixed baseline rebuilt`
  - 它不能单独证明 promotion readiness
  - 缺失的 `sample_size / Layer 3 / gate-report closure` 仍必须保留为独立 blocker

## 我实际跑了什么验证

- 复核并引用了以下 authority source：
  - `OpenEmotion/docs/archive/mvp11/T07_3_MIXED_LAYER2_RERUN.md`
  - `OpenEmotion/docs/archive/mvp11/MVP11_5_READINESS_CRITERIA.md`
  - `OpenEmotion/artifacts/roadmap/evidence/MVP11_5_T07.3.md`
- 已把分流结果同步进：
  - `runtime/stage2_readiness_decision.json`
  - `runtime/RUN_STATE.json`
  - `runtime/SESSION_HANDOFF.md`
  - `reports/stage1_blocker_dossier.md`

## 还没证明什么

- 还没证明 `numeric_leak` 已被修掉。
- 还没证明 `sample_size / Layer 3 natural evidence / gate-report closure` 已补齐。
- 当前仍不能宣称 `Stage 2 ready`，下一步只能执行第一个 bounded strengthening repair，然后 rerun + recompute。
