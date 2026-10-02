# EGO / SharedField — v0.6 project entry

## 已确认目标
持续成长 > 长期经历/约定连续性 > 理解情绪与自然交流 > 自发兴趣与目的 > 实时相处 > 电脑/MC陪玩。日常拟人交流，但不虚构经历、动作或已证实主观体验。不得把宽目标替换为任务助手、人格prompt、关系记忆产品。

## 当前默认入口
`START_WINDOWS.bat` / `python run.py memory` → `switchlab/memory/http.py` → `MemoryService` → `MemoryStore`。本地SQLite为长期事件、有效状态、来源、前瞻候选、结果学习的共同载体。旧`shared`/`studio`/数值`serve`仅为兼容和研究对照。

本版工程目标：口头约定当轮可靠写入；改约/取消版本生效；有限上下文按需读原文；无新用户消息仍可检查有效约定；真实联系结果能改变下一次有限等待/联系选择；跨重启/导出恢复。

## 边界
没有读取或修改用户EGO/ITL仓库；这是对话压缩包内的离线工作副本。没有真实云模型语义测试、Windows实机测试、原生浏览器回环访问验证。后台是本地进程内功能，不是本次ChatGPT自动任务，不是系统开机自启。

默认联系结果预测采用更强的简单类别后验；SGD为保留的研究臂，自动重放OFF。检索是FTS+版本关系+有限查询/原文读回，没有向量模型。不要把它写成完整架构或终身神经学习。

## 继续前先读
1. README.md 与 VALIDATION.md：使用、实际验收及限制。
2. docs/memory/EGO_Memory_Architecture_v1.md：用户批准的完整设计。
3. docs/memory/EGO_SharedField_Requirements_v2.md：需求顺序和场景。
4. docs/memory/IMPLEMENTATION.md 与 HANDOFF.md：本次实现映射与下一步。
5. evidence_v06/final2_tests/、final2_scale_100k/、final2_browser/：结果，不以旧版本日志替代当前运行。

下一步不是加地图或更多恋爱台词，而是用真实模型验证口头约定/纠正/否定/相近对象的语义链，补足观察与可塑理解；具体预算和权限另配置。任何真实语义错误要单列，不能用绿色数据库测试掩盖。
