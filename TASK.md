# GOAL
完成 `/home/moonlight/Desktop/OpenEmotion/MVP-7.txt`：在 MVP-6.2.3 稳态上实现 Self-Model v0 + Episodic Memory v0 + Self–Other Boundary v0 + Offline Rollouts v0（默认关闭），并满足回归与新增 smoke 验收。

## Definition of Done (DoD)
- [x] A1 回归不破坏：Eval v2.3 --all 保持 15/15 PASS
- [x] A2 既有 smoke 4 项持续 PASS
- [x] A3 强制无分化负例 sanity 必须 FAIL（防永远 pass）
- [x] B1 新增 smoke_self_report_alignment PASS
- [x] B2 新增 smoke_self_other_boundary PASS
- [x] B3 新增 smoke_continuity_preference PASS
- [x] B4 新增 smoke_confabulation_trap PASS
- [x] C1 eval 输出包含 threshold_config.version/hash + candidate_param_hash
- [x] C2 --debug-metrics 默认关闭；off/on 不影响最终判定
- [x] C3 --enable-rollouts 默认关闭；关闭时行为等价基线
- [x] D1 文档交付：docs/MVP-7.0-self-model.md
- [x] D2 文档交付：docs/SCENARIOS-self-awareness.md

## Current status
- last_update: 2026-03-02 08:25 CST
- phase: done
- next_action: None (MVP-7.0 complete)
- blockers: None

## Commits (MVP-7.0)
- dcb1852 feat(mvp7): US-704 offline rollouts v0 + DMN tick + D1/D2 docs
- 60e1e4d feat(mvp7): add --enable-rollouts CLI parameter (default False)
- 5e3d4b8 feat(mvp7): meta cognitive override + OOD scenarios + self-model smoke tests
- 795bc4c feat(mvp7): deterministic OOD generation with seed + manifest output

## Test Results
- 2047 passed, 10 skipped, 251 warnings
- Eval v2.3: 15/15 PASS
