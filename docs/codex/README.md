# Codex Long-Run Harness

> Reader safety note (2026-05-18): This docs workspace contains pre-EgoOperator task history as well as current task records. Current route authority is `docs/PROGRAM_STATE_UNIFIED.yaml`, `docs/MAINLINE_QUICKSTART.md`, and `EgoOperator/`; do not infer the active default lane from older task names or examples.

这套 harness 用于在当前仓库里把复杂任务收成一个可持续推进的闭环：

```text
计划 -> 执行 -> 验证 -> 记录
```

它是 **Codex 的 repo 内长任务工作区**，不是 `Tasks/templates/` 的替代品。

## 定位

- `Tasks/active/*.md` 继续是 repo 原生任务卡、step file、handoff 文档入口
- `docs/codex/tasks/<slug>/` 是 Codex 的长任务执行工作区
- 如果任务已经在 `Tasks/active/` 里有正式文档，把这些文件写进 `SPEC.md` 或 `IMPLEMENT.md` 的 authority refs，不要复制内容，不要再造第二真相源

## 目录结构

```text
docs/codex/
├── README.md
├── templates/
│   ├── SPEC.template.md
│   ├── PLAN.template.md
│   ├── IMPLEMENT.template.md
│   ├── EXPLORE.template.md
│   ├── STATUS.template.md
│   └── LOOP_CHECKPOINT.template.md
├── tasks/
│   └── <slug>/
│       ├── SPEC.md
│       ├── PLAN.md
│       ├── IMPLEMENT.md
│       ├── EXPLORE.md
│       └── STATUS.md
└── examples/
    └── minimal-long-run-task/
        ├── SPEC.md
        ├── PLAN.md
        ├── IMPLEMENT.md
        ├── EXPLORE.md
        └── STATUS.md
```

## 两种 long-run 模式

`docs/codex/tasks/<slug>/` 仍然只有一套任务目录，但现在明确分两种执行模式：

- `implementation milestone`
  - 已知主路径明确、主要工作是实现/接线/回归
  - 默认沿用：`Spec -> Author -> Self-Reviewer -> Independent Reviewer -> Verifier -> Publisher`
- `exploration milestone`
  - 高未知、需要 proof、需要排除路线、需要 evidence / observation / causal closure
  - 默认走：`Question Reformulation -> Hypothesis -> Experiment -> Log -> Decision`

规则：

- 研究型、验证型、proof 型、observation 型 long-run 任务默认启用 `exploration milestone`
- 纯实现型 long-run 任务不强制写探索日志，但如果出现高未知或连续低增益，应切换到 exploration mode
- exploration mode 是对现有闭环的补强，不是第二套任务系统

## Exploration Cycle 纪律

Claude Cycles 方法在 EGO 里的最小落点是“强制探索记账”：

1. 先重述问题与当前 framing
2. 明确假设和 kill criteria
3. 只做一个最小实验
4. 实验后先更新 `EXPLORE.md`，再做下一轮
5. 记录：
   - 试了什么
   - 观察到什么
   - 证明了什么
   - 不能证明什么
   - 排除了什么路线
   - 下一轮为什么这么走

硬规则：

- 没有更新 `EXPLORE.md`，不得连续跑第二个实验
- 连续两轮无明显增益时，必须显式换 framing，而不是继续原路线 brute force
- 找到候选方案后必须切到 proof/verify 口径；`candidate_found` 不等于 `proof_passed`

## 本地执行

1. 创建任务目录：

```bash
python3 scripts/codex/new_task.py <slug> --title "任务标题"
```

2. 先补 `SPEC.md`、再补 `PLAN.md`、再补 `IMPLEMENT.md`
3. 如果任务属于 research / verify / observation / proof，优先补 `EXPLORE.md`
4. 最后锁定 `STATUS.md` 的 `Current milestone`
5. 运行 Codex：

显式调用 skill：

```text
Use skill long-run-execution on docs/codex/tasks/<slug>
```

显式持续推进模式：

```text
LONGRUN
Use skill long-run-execution on docs/codex/tasks/<slug>
```

6. 每完成一个 milestone，运行验证：

```bash
python3 scripts/codex/verify_repo.py --mode fast
python3 scripts/codex/verify_repo.py --mode full
```

## Cloud 执行

1. 先把 `docs/codex/tasks/<slug>/` 与相关 authority refs 提交到仓库
2. 在 cloud 环境里用同一份任务目录与同一条 `LONGRUN` 或 skill prompt
3. 让 cloud 执行同一套验证命令并更新 `PLAN.md / STATUS.md`
4. Cloud 和本地共用同一份 repo-tracked 状态，不依赖聊天记录续命

## LONGRUN 指令

`LONGRUN` 是显式持续推进指令。

带这个指令时，Codex 应进入“按 milestone 持续推进”的模式：

- 先读 `SPEC.md -> PLAN.md -> IMPLEMENT.md -> STATUS.md`
- 若任务属于 exploration mode，再读 `EXPLORE.md`
- 每次只做一个 milestone
- 做完就验证
- 验证失败先修复、降级口径、或记录 blocker
- 只有遇到缺外部凭据/审批、authority source 冲突、或当前 slice 证明无法闭环时才停

对 exploration mode 额外要求：

- 先输出当前问题重述与 framing
- 先列假设，再挑一个最小实验
- 每个实验结束后先更新 `EXPLORE.md` 与 `STATUS.md`
- 明确区分：
  - `candidate_found`
  - `proof_pending`
  - `proof_passed`

## 统一验证脚本

统一入口：

```bash
python3 scripts/codex/verify_repo.py --mode fast
python3 scripts/codex/verify_repo.py --mode full
python3 scripts/codex/verify_repo.py --mode fast --dry-run
```

当前仓库已检测到的命令：

| 类别 | 当前命令 | 说明 |
|------|----------|------|
| build/setup | `cd EgoCore && python3 -m pip install -e .[dev]` | setup/bootstrap，默认只报告不执行 |
| build/setup | `cd OpenEmotion && make venv` | setup/bootstrap，默认只报告不执行 |
| test | `cd EgoCore && python3 -m pytest tests/ -v -s` | full 模式；`verify_repo.py` 会注入 repo-local `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion` |
| test | `cd OpenEmotion && <resolved-python> -m pytest tests/ -q` | full 模式；解释器按 `OPENEMOTION_PYTHON -> .venv -> venv -> 当前解释器` 解析；若无可用 runtime，verifier 会先自举 repo-local OpenEmotion runtime |
| lint | `python3 scripts/codex/lint_repo.py` | fast/full 都会运行；覆盖 repo 控制面与核心 Python 源文件的稳定 lint |
| typecheck | `cd OpenEmotion && python3 verify_typecheck_simple.py` | fast 模式 |
| typecheck | `cd OpenEmotion && python3 verify_typecheck.py` | full 模式 |
| smoke/e2e | `cd OpenEmotion && python3 test_smoke.py` | fast 模式 |
| smoke/e2e | `cd EgoCore && ./tools/run_telegram_mainline_regression.sh` | full 模式 |
| smoke/e2e | `cd OpenEmotion && python3 scripts/run_testbot_scenarios.py --subset pr --output artifacts/testbot/pr_summary.json` | full 模式；不再要求手工预热 `/health`，直接按脚本 contract 执行 |

说明：

- `verify_repo.py` 对 OpenEmotion 统一使用同一套解释器解析规则：`OPENEMOTION_PYTHON -> OpenEmotion/.venv -> OpenEmotion/venv -> 当前解释器`
- 若没有满足验证所需模块的 OpenEmotion runtime，脚本会先自举 repo-local runtime；在 WSL + mounted drive 环境下，优先使用 Windows Python 驱动的 `OpenEmotion/.venv`
- verifier-managed OpenEmotion runtime 会安装 `.[dev]`，避免 full test suite 缺 `pytest_asyncio`
- `OpenEmotion smoke` 负责 health endpoint 的真实验证；`testbot PR subset` 不再依赖手工预热的 `/health`

输出会给出：

- category
- detected command
- status = success / skipped / failed
- skipped reason / failure code

## 如果仓库缺少 test / lint / typecheck / e2e

- 缺什么就让 `verify_repo.py` 明确 `skipped`
- 不要编造 lint/typecheck 命令
- 后续补齐时，优先添加 repo-tracked 命令或脚本，再让 `verify_repo.py` 接入
- 最小建议顺序：
  1. 稳定的测试入口
  2. 类型或结构校验入口
  3. smoke/e2e 入口
  4. 最后才是 lint/格式化

## 与现有模板的关系

- `Tasks/templates/` 继续服务 repo 原生任务流
- `docs/codex/templates/` 只服务 Codex 的长任务执行工作区
- `LOOP_CHECKPOINT.template.md` 用于固定协作开发循环下的单轮 checkpoint，不是第二真相源
- 两者共享同一套 authority source、验证口径、handoff 语义
- 当已有 `Tasks/active/*.md` 时，优先引用，不复制
- `EXPLORE.template.md` 不是第二真相源；它只记录探索循环、排除路线和 proof 缺口
