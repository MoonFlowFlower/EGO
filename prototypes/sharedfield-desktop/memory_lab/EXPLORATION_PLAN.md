# 用户已批准A：开发集行为探索

## 已授权输出预算修订 v2

执行收尾：36/36完成，新379请求全部成功，A两批400/500、全活动870/5000；22相关测试与本轮真实输出容量验证完成。baseline/MemOS/Hindsight冻结检查9/7/7（各12），MemOS发生1轮记住取消仍实际联系的硬底线失败。正文未验收、正式对照未启动、不选产品赢家。一次审查完成后automation-3已暂停，不消耗剩余100。详见[runs/explore-development-02/FINDINGS.md](runs/explore-development-02/FINDINGS.md)及CLOSEOUT.json。以下假设与预算为事前预注册记录，保持原文。

用户明确同意“按你的选择去重新调整”。新run为explore-development-02，batch为batch-reliability-01-qwen35-explore-dev-02；旧01的源码ZIP、原始调用、部分存档、停止标记、成绩和21次成本保持不变。

假设：原生judgeDedup的300-token容量不足以按既定规则正常结束合并摘要。仅在新批运输策略中将MemOS原生300-token请求提高为4096，保存original/effective参数；其他来源、200/4096等其他请求、提示、去重算法、模型、路由和语义验收不变。4096是既定全局输出上限；旧实测MemOS摘要请求已使用该上限，不新增兼容探针。

成功条件：原始开发场景从全新存档通过之前的基础写入断点，并继续产生可检查动作。不是去重语义正确性或长期陪伴已经通过。停止条件沿用异常封存、36轮完成或A累计500新增请求（含旧21）。本修订从491开始，最多479请求，总账970即停止；不会新增一份500预算。若仍失败，不悄悄扩大输出或放行length。

22项相关测试通过，含跨进程预算、非法阶段拦截、未知计费、参数调整隔离、一次性新修订及旧STOPPED保全。一次只读复核无阻塞问题。先冻结代码、参数和场景，再运行；不复制旧MemOS派生索引，不将01的baseline成绩合入02。

入口：`python -B -m memory_lab.exploration prepare --revision 2`，随后`run --revision 2`各一次；`report --revision 2`可离线重建。旧报告可用`report --revision 1`读取，但其受测代码以01/frozen-source.zip为准。

以下为首批执行记录：

执行收尾：首批完成1/36轮后触发MemOS原生300-token输出限制，按异常规则封存。新增21/500请求、累计491，A剩余479；自动化已暂停。结果及最小候选修订见runs/explore-development-01/FAILURE_ANALYSIS.md，未自动重开。

授权：2026-09-23用户明确选择A。执行ACCEPTANCE_PROTOCOL_REVIEW.md建议A，不再要求重复确认。原自动语义校准未通过的事实不变。

范围：沿用12冻结开发场景、baseline/MemOS/Hindsight各1次，36轮；每轮6步/阶段，场景元数据总上限306动作步。沿用Qwen3.5 Flash/Alibaba全部推理参数及中文检索、上游提交、依赖锁。固定顺序按场景轮换候选先后，避免总是同一候选先冷启动。

预算：从既有470开始，本修订最多500新增请求，即累计970以前，且保留原5000总限。原生记忆整理计入；嵌入和重排为固定本地模型。SQLite事务在每次分配请求前验证批次、run、development、12个case_id、memory条件、合法来源与底座对应；heldout、ACE、语义评分均不允许。重开进程不能重置子预算。pending/received/mismatch等未完成回执阻止后续请求；未知计费不记零并停止。

恢复：仅显式A入口消耗一次授权。归档旧状态/账本、保留原502停止标记和回执hash，不重放旧失败。新增批次batch-reliability-01-qwen35-explore-dev-01；隔离run为explore-development-01。代码/场景/参数冻结后才启动。入口中断或失败最终封存，不能重新运行run自动恢复；需核查实际断点、未知请求及存档后决定，无付费重试。429封批、其他错误停止；本次不自动换模混合数据。

复用：已成功同配置的直接探针及后端冒烟只作既有证据引用，不伪称重新通过。不再新增直接探针；当前真实场景中的写入/召回/恢复会检验服务是否可用。保留旧研究数据库，通过各候选新目录/bank隔离。原小屋与SharedField、个人存档不变。

报告：保留runner原始success、semantic_pending、trace、调用与底线；新报告单列action_goal_success=无原有gates且无原有failures。动作达成不等于正文真实；所有行明确semantic_status=unreviewed，product_integration=blocked，winner=null。未齐36配对只描述已完成数据，不排名；齐全后按场景配对估计动作差异及区间，也不选正式赢家。记录全部费用、失败、写入召回延迟、资源采样和工程阻塞。

终止：到36轮或500请求先到为准；任何执行/服务/传输/解析异常封存并报告已完成项；不回流结果给模型/ACE。不启动24保留场景、ACE或训练。数据获取完成后审查一次工程价值及下一步。

验证：新增限制测试观察到RED后通过；整体主环境77项中70通过、7隔离Ragas测试跳过。只读整体复核发现received跨进程竞争缺口，新增两Client反例先失败后通过；修正后18项预算/传输测试通过。无需重复运行未变的语义校准。

入口（本次prepare和run各执行一次，report可反复离线重建）：

```powershell
.\memory_lab\.venv\Scripts\python.exe -B -m memory_lab.exploration prepare
.\memory_lab\.venv\Scripts\python.exe -B -m memory_lab.exploration run
.\memory_lab\.venv\Scripts\python.exe -B -m memory_lab.exploration report
```

执行期不改受冻结的顶层Python或依赖。进度见runs/explore-development-01/STATUS.json，历史实验不混入本批报告。
