# 桌宠记忆与成长实验

最新 `readiness-v7` 因本地缺action协议错误封存，2/3案例完成；累计945、原A剩25。仅离线报告可重建：`python -B -m memory_lab.action_diagnostic report --revision 7`；prepare/run禁止重入。源码/案例/协议已冻结，接续请先看 `PROGRESS.md` 与 `runs/readiness-v7/FINDINGS.md`。

以下为历史：

当前接续以 `PROGRESS.md` 为准。最新 `state-feedback-v6` 已封存（累计938，原A剩32）；prepare/run均不可重入。可离线重建本轮报告：`python -B -m memory_lab.action_diagnostic report --revision 6`。冻结源码/案例/协议和原始调用见 `runs/state-feedback-v6/`；不能在旧冻结结果上混用当前改动，不能重置账本复跑。

以下为历史入口：

最新：用户已批准开发集行为探索A，见`EXPLORATION_PLAN.md`。新入口`python -B -m memory_lab.exploration prepare/run/report`；prepare/run各一次，报告可离线重建。最多36开发轮/500新增调用，复用原470累计账本；语义待验收、无正式排名、无保留集/ACE。以下446等记录属于历史校准断点。

这是**真实模型调用下的模拟生活实验**。独立于 SharedField 原运行时与个人存档；不会恢复共同阅读任务，不接入电脑观察/控制，也没有完整房间界面。

历史 batch-01 的旧诊断不混入新比较。reliability-01 / fragment-v4 已因供应商嵌套502停止：校准完成56/60，53例匹配冻结标签；两例有样本标注歧义，另有一例安全拒判。此前三处片段组装误拒本轮均通过，但整体语义门槛尚未通过。累计446次请求（443成功、3失败），保留原5000次预算。未重试或换模型；正式记忆0/216、成长0/144。见 `REPORT.md` 与 `evidence/fragment-v4-adjudication.md`。

## 入口

在项目根目录的 PowerShell 中运行：

```powershell
.\memory_lab\run.ps1 test
# 本轮已关闭；此命令只重建报告，不调用模型
.\memory_lab\.venv\Scripts\python.exe -B -m memory_lab.status_report --campaign reliability-01
# 本轮显式修订会归档旧失败并沿用同一个5000次账本；不要另建活动重置额度
# 本轮调用（已使用，不能重复执行同名修订）：
# .\memory_lab\.venv\Scripts\python.exe -B -m memory_lab.campaign --id reliability-01 --revision frame-v3 --calibration-cases memory_lab/scenarios/semantic-frame-v3-combined.json
# 后续独立获批的活动才使用新的活动ID
# .\memory_lab\run.ps1 campaign -Campaign <new-campaign-id>
.\memory_lab\run.ps1 stop
```

原批次停止标记不会被清除。429封存该模型的全部阶段，顺序尝试 DeepSeek、Qwen3.7 Flash、Qwen3.5 Flash、Gemini 2.5 Flash-Lite；每个模型固定供应商。换模型重建全部基础记忆、重跑记忆比较和ACE教学/对照。配置不兼容只可在探针阶段跳过，不能依据正式得分挑模型。

`test` 不调用付费模型。实验与语义校准调用 OpenRouter；同一活动的5000次总额度涵盖所有模型、探针、废弃批次和评分，切换不重置。已保存的有效响应按输入和调用上下文复用；未知计费/超时停止。动作、世界状态、约定、经历和索引发件箱原子提交，恢复只补未完成步骤。原生写入不能确认完成时重建派生索引；删除也通过持久队列交付。完整批次和已停止的活动不能自动重新打开。

评测依赖独立安装：`uv venv --python 3.11.15 memory_lab/.eval-venv`，然后 `uv pip sync --python memory_lab/.eval-venv/Scripts/python.exe memory_lab/requirements-eval.lock.txt`。固定 Ragas 0.4.3 与兼容 LangChain；不会升级实验运行环境。`setup` 安装原实验依赖，评测环境使用此单独入口。

环境：Windows + WSL2 Ubuntu、Docker Engine（本次研究安装在 WSL）、Node 22、uv；Python 3.11.15。首次复现运行 `run.ps1 setup`，会按锁文件安装隔离依赖、固定上游、下载中文模型，不开始付费推理。需要 WSL 已有 Docker 和 `/root/.local/bin/uv`。本研究服务允许这些依赖，最终桌宠免手动部署仍是后续产品目标。

真实 key 仅从 `D:\Project\MyAIWorkspace\openrouter.txt` 的 **codex key** 条目读入网关进程，不复制入实验配置。`state/gateway-token.txt` 是单独随机生成的本地网关令牌；容器只持有此本地令牌。不要提交 `state/`。数据库端口不发布，API与控制网关仅面向本地/WSL桥接地址，无系统防火墙改动。

## 设计与公平性

- 三个后端共享原始事件、持久约定、观察、动作、检索预算、行为模型和执行器。基线使用 BGE-m3 语义检索与中文双字全文索引，以 RRF 融合；不是只保留近几轮聊天的弱基线。
- Hindsight 使用 v0.10.1镜像固定digest、PGroonga、pgvector、同一BGE-m3、多语言 bge-reranker-v2-m3；保留默认事实/观察加工。MemOS只加载原生 `src/index.ts` 独立插件，关闭分享、遥测和自动技能，不加载OpenClaw宿主入口。
- `Store` 管事实来源、约定、经验、动作去重；检索摘要本身不能冒充来源。`World` 的查看/拿取/进食/睡眠/留信/联系/求助实际改变实验状态。
- 环境事件、时钟和需要都会触发检索；无需用户重新提问。演员只收到 `public_phase`、观察和召回证据；`expect/forbid` 只在评分器中使用。
- `scenarios/manifest.json` 固定12开发/24保留，保留每个3次。各次从相同基础索引复制独立状态，无跨案例测试反馈。人物与物品在开发和保留中不同；这些是合成场景，不代表独立用户。
- ACE使用锁定官方Reflector、Curator、playbook增量操作，替换运输和反馈接口；没有修改其学习算法，没有训练模型权重。输入开发教学、用户反馈、实际执行回执，明确没有题目标准答案。学习完冻结，两个成长条件都拿到相同开发经历；只ACE条件增加已冻结经验。
- 同一正式比较的全部推理和语义审计固定到一个 profile，temperature=0、top_p=1、seed=20260923、供应商禁止隐式回退；回执校验实际模型与供应商。固定seed不保证字节级确定性。
- 语义审计使用 Ragas 官方事实拆解和支持性核验提示/类型，通过统一计费网关调用。校准失败不继续正式比较；未审计、证据不足和无法确定的关键陈述不能当作通过。评分只写独立审计记录，不回流给行动模型或ACE。
- ACE经验按条目保存适用范围、来源、版本和前置经验。使用全部输入来源保守追踪，不能只相信模型自报引用；删除时失效关联经验、派生行动记录和活动记忆，物理生活状态保留。失效前轨迹不得重新教出删除内容。

## 数据、恢复与证据

`runs/<run>/bases`保存一次基础索引，`episodes` 每个候选/条件/场景/重复独立。每步包含检索原文、来源ID、模型回执ID、动作、执行回执与状态。`runs/batch-*/calls`保留请求、响应、用量、费用、耗时及失败，超时的计费状态标记未知，绝不当作零费用。

导出包含原始事件、约定状态、经验版本/来源、世界状态和动作去重信息。基线/MemOS复制关闭后的本地数据库；Hindsight使用官方transfer ZIP导出导入新bank（重复实验的初始隔离用原生clone）。原始审计材料与可召回记忆分开：来源删除清除当前记忆及相关派生内容；被冻结的合成测试输入、审计结果仍作为实验记录保留，不再提供给演员。

`licenses/`、`upstream-lock.json`、`model-revisions.json`、Python locks、npm lock记录版本与许可证。MemOS主仓许可证与local插件package中的MIT声明不同，分组件保留，不能把整仓统一视为MIT。锁定版本的完整OpenClaw宿主构建有类型错误；独立插件的类型检查命令：

```powershell
.\memory_lab\vendor\MemOS\apps\memos-local-openclaw\node_modules\.bin\tsc.cmd -p .\memory_lab\memos-tsconfig.json
```

资源文件 `runs/resource-samples.jsonl` 是有时间戳的采样峰值，并不声称捕获每个瞬时峰值。共享本地向量/重排模型的内存与候选数据库/进程要分别报告，不能把全部共享开销归给某一候选。

## 验收边界

报告分开列硬底线、行动/迁移/主动联系/分享适应、费用和延迟。配对统计先按场景平均三次重复，再做分层bootstrap。没有明确收益保留简单基线；ACE无可重复收益不默认接入，也不由此自动转向更昂贵训练。

通过模拟测试并不代表“复刻了人性”。真实共同活动、长期关系、性格稳定性、权限、UI/Live2D以及用户实际感受到的陪伴，都必须在后续桌宠中验收。当前执行状态见 `PROGRESS.md` 和项目根 `TASK_BOARD.md`。
