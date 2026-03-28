# Independent Review — STAGE2-01 and STAGE2-04

## Findings

1. `STAGE2_01_mvp11_5_execution_contract.json` 仍残留错误命令，和环境备注/基线报告不一致。
2. stop rule 对 `V4/E4` 的适用范围写得过粗，会把负向 readiness 判定也误判成必须立即 stop。

## Resolution

- 已把执行契约修正为：
  - checker baseline 走 `EgoCore/.venv` + `-s`
  - mixed rerun 走 `OpenEmotion` cwd 下的脚本直跑
  - intent alignment E2E 走 `EgoCore/.venv` + `-s`
- 已把 `V4/E4` 门限收口为：
  - 只对 `ready / promote` 正向宣称强制
  - `not_ready / stay_stage1` 允许以 `V3/E3` 记录，只要直接对齐当前 rerun artifact 与 criteria

## Reviewer Conclusion

- 当前未发现 “Stage1→Stage2 与 MVP12+ 路线混淆” 的阻断项。
- 在上述修复后，本批次可以合法停在 `STAGE2-05` 并继续做 bounded repair，不构成 overclaim。
