# OpenEmotion Candidate Hash Stabilization - PLAN

## Task summary

这是一个 bugfix slice。当前层级是实现/验证层，目标是修复 `candidate_hash.py` 中的工作树定位错误，让报告注解在当前仓库环境下可稳定取到 `code_version` 或安全降级。

## Milestones

### Milestone 1: Reproduce candidate-hash failure

- scope: 复现目标测试，确认失败仅来自硬编码 git cwd
- files / areas likely touched:
  - `OpenEmotion/tests/test_candidate_hash.py`
  - `OpenEmotion/scripts/candidate_hash.py`
- acceptance:
  - 明确失败点不在 hash 计算本身，而在 `code_version` 注解
- validation:
  - `/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/.venv/Scripts/python.exe -m pytest OpenEmotion/tests/test_candidate_hash.py -q`
- rollback note:
  - 若失败面比预期更大，先停在分析层，不扩到无关测试

### Milestone 2: Dynamic git worktree resolution

- scope: 用 repo-local 动态路径替代硬编码 cwd，并保留 `unknown` fallback
- files / areas likely touched:
  - `OpenEmotion/scripts/candidate_hash.py`
- acceptance:
  - 目标测试转绿
  - 版本探测在非 git 或异常环境下不抛错
- validation:
  - `python3 -m py_compile OpenEmotion/scripts/candidate_hash.py`
  - `/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/.venv/Scripts/python.exe -m pytest OpenEmotion/tests/test_candidate_hash.py -q`
  - `python3 scripts/codex/verify_repo.py --mode fast`
  - `python3 scripts/codex/verify_repo.py --mode full`
- rollback note:
  - 若动态路径解析误判，回退到只用当前脚本父目录或直接返回 `unknown`

## Progress

- current_status: verification completed
- current_milestone: Milestone 2
- milestone_state: complete

## Decision log

- 2026-03-29: 不改 hash 算法，只修 `code_version` 注解的路径契约
- 2026-03-29: 版本探测改为从脚本位置向上查找 `.git`，失败时返回 `unknown`

## Surprises / discoveries

- 目标测试失败面完全收敛到 `subprocess.check_output(... cwd=<dead linux path>)`
- 当前仓库里从 OpenEmotion 子目录执行 `git rev-parse HEAD` 就足够，不需要硬编码绝对路径

## Outcomes / retrospective

- 本轮已证明：动态 worktree 解析足以替代硬编码路径
- 还没证明：全仓 `full verify` 全绿
- 下一步最小闭环动作：把该失败面已离开 full summary 的证据写回状态，并切到下一条独立失败面
