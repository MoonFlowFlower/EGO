# OpenEmotion Candidate Hash Stabilization

## Goal

稳定 [test_candidate_hash.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/tests/test_candidate_hash.py)，消除 Windows 环境下 `code_version` 注解逻辑因硬编码 git cwd 失效而导致的失败。

## Non-goals

- 不修改 candidate/threshold hash 算法
- 不处理其他 OpenEmotion pytest 失败面
- 不改文档或业务功能

## Constraints

- 边界约束：只修版本探测层，不放大到 hash 逻辑或报告结构重构
- 仓库/子仓约束：改动限定在 OpenEmotion 脚本和本 slice 文档
- 环境约束：必须兼容 Windows 和当前仓库真实工作树
- 发布约束：最小 patch，可直接通过目标测试验证

## Acceptance criteria

- [x] `OpenEmotion/tests/test_candidate_hash.py` 全绿
- [x] `annotate_report_with_hashes()` 不再依赖失效的 Linux 绝对路径
- [x] git 不可用或不在工作树时，`code_version` 仍安全降级为 `unknown`

## Known risks / dependencies

- 风险：full verify 仍可能被其他独立失败面阻塞
- 依赖：本地 `git` 可用时应返回真实短 SHA
- 外部 blocker：无

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- [test_candidate_hash.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/tests/test_candidate_hash.py)
- [candidate_hash.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/scripts/candidate_hash.py)
