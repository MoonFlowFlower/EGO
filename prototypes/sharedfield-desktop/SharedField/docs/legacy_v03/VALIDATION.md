# SwitchLab Adaptive Studio v0.3 — 实际验证与未验证范围

## 本次实际执行

本轮从完整v0.2上传包重建集成，继承上一轮留下的neural.py和设计，不把未提供的v0.3集成代码假称为已恢复。没有访问用户EGO/ITL仓库或用户电脑。

| 验证 | 本次结果 | 原始记录 |
|---|---|---|
| 完整Python套件 | **169项通过，0失败、0错误、0跳过** | evidence_v03/final_tests/result.json、final_tests.log |
| 实际普通对话路径 | analyse → 本地选择 → express；下一次真实输入更新本地网络 | test_adaptive_core.py、test_adaptive_service.py |
| 学习真实性 | 隐藏层/输出层梯度、有限差分、权重保存恢复、标签撤回重建 | test_adaptive_learning.py |
| 冻结与重放 | 冻结停止预测器和能力/技能新增学习；重放执行梯度但不增加外部样本 | test_adaptive_learning.py、test_adaptive_core.py |
| 目标实际执行 | 提案未表达不执行；实际草稿、反馈、修订、实际lab动作进入同一回路 | test_adaptive_core.py、test_adaptive_pipeline.py |
| 两段实际HTTP | 客户端→实际应用HTTP→实际兼容端点HTTP→选择→表达→草稿→反馈→修订→复算 | test_adaptive_pipeline.py；语言端为明确TEST_FIXTURE |
| 并发/暂停/恢复 | 新观测丢弃迟到输出；失败不提交未表达目标；重启暂停 | test_adaptive_service.py |
| 两阶段供应商协议自检 | 临时状态2次请求协议；不训练真实生命周期 | test_adaptive_service.py；夹具，不是真实服务商 |
| UI交互 | **14项通过，无JS页面错误；390px无横向溢出** | evidence_v03/current/browser/result.json、desktop.png、mobile.png |
| 旧版本迁移 | 原版v0.2源码复算旧记录，再导入历史；拒绝篡改与覆盖 | test_adaptive_migration.py |
| Python3.10语法 | 实际解析通过，不是3.10实机运行 | evidence_v03/current/python310_syntax.json |
| JS语法 | node --check 通过 | 实际构建命令；浏览器另行执行脚本 |

环境：**Linux、Python 3.13.5、Chromium 144.0.7559.96**。未在Windows/macOS实机运行。运行程序不需要Playwright；它只是可选开发验证工具。

原v0.2有120项回归测试。本轮保留其测试范围，但两处期望按新版合同更新：静态界面标题改为“持续认知工作台”；默认studio-import只接收可由v3启动的状态，原覆盖保护测试改用v3样例。增加了拒绝不可启动v2导入的回归，不是删掉失败用例。

一次包含训练和全套测试的组合命令触及45秒工具超时，不能算通过；随后单独完整执行得到上表结果。历史RED/超时日志保留于current目录，最终判断以final_tests为准。

## UI验证限制

**原生浏览器访问本机地址确实尝试过，返回 ERR_BLOCKED_BY_ADMINISTRATOR。没有修改、移除或规避受管理浏览器策略。**

随后使用 `page.set_content` 加载真实HTML/JS/CSS，以及显式的in-process TestTransport，把UI操作交给真实AdaptiveService。测试语言输出始终带TEST_FIXTURE标记。这能验证交互与服务状态，但**不验证原生浏览器→HTTP，也不验证set_content之外的CSP实际执行**。真实HTTP路径及响应头有独立自动化测试，不能把两部分拼称原生浏览器端到端通过。

UI试跑中两次失败来自编写的夹具：颜色触发词与输入不匹配，以及夹具对结构化内部事件生成了非逐字原文。修正夹具后14项通过；没有放宽产品的来源校验。历史失败状态仅供调试，不是最终结果。

## 实际学习比较：神经网络未胜出

调用：`python run.py cognitive-benchmark --out evidence_v03/current/benchmark`。

4个独立生成种子；每个种子160条训练观测、64个留出情境；每种方法得到相同观测历史、测试时不更新。标签来自未知非线性函数的合成生成器。它是有限离线预测/选择测试，不是现实长期收益评测。

| 方法 | 测试MSE ↓ | 平均后悔值 ↓ | 最优动作比例 ↑ |
|---|---:|---:|---:|
| 小神经网络 | 0.126171 | 0.307760 | 52.7% |
| 经验匹配 | 0.031720 | 0.035502 | 88.3% |
| 默认误差选择 | 0.031720 | 0.035502 | 88.3% |
| 固定先验 | 0.124980 | 0.351252 | 46.5% |
| 知道真实生成函数的oracle | 0 | 0 | 100% |

结果不支持神经方案优越性。因此默认选择器能够选简单方法；没有修改标签或指标把神经网络改成“赢”。未完成history-conditioned Transformer、长上下文LLM、跨episode meta-learner、amortized learner的公平比较，不得声称架构超越这些基线。

## 重放与遗忘

两项确定性任务，在学习任务B后测任务A：

| 条件 | 真实样本 | 总梯度次数 | A最终MSE ↓ | B最终MSE ↓ |
|---|---:|---:|---:|---:|
| 不重放 | 200 | 200 | 0.230238 | 0.009170 |
| 重放旧经历 | 200 | 400 | 0.018184 | 0.003276 |
| 等计算但仅强化当前任务 | 200 | 400 | 0.343871 | 0.001882 |
| 按任务键查表 | 同一任务信息 | 不适用 | 0 | 0 |

这个小实验支持“重放在该网络/任务条件下减轻干扰”的有限结果；当前任务多训练取得更低B误差，存在权衡。查表饱和两任务，所以不证明神经结构必要，更不证明终身学习。

## 历史干预与主路径

固定同一候选组、只改变过去的合成反馈，通过真实Core.message/analyse/express/outcome入口分别构建两个生命周期。偏好compare的历史最终选择compare，偏好direct的历史选择direct；两者都有可重新执行的checkpoint。它证明这段实现的候选选择依赖历史，不证明反馈合理、不证明真实世界变好、不证明潜在社会建模。

样例 `examples/adaptive_sample.json` 经实际草稿写入、失败反馈、修订、成功反馈、后续观测与重放构造；包含11个事件、2份草稿、11次梯度更新。所有语言内容/标签均明确为TEST_FIXTURE。不是用户默认记忆。打包交付后从新解压目录再次复算的结果以包外delivery_verification.json为准。

## 没有验证或没有实现

- 没有请求真实云模型，没有启动本地大型语言模型；缺少服务商密钥/真实模型授权，未擅自读取用户凭据。语义能力、反迎合、自然交流体验和协议真实通过率均为unknown。
- 没有证明相对普通LLM多轮聊天的净收益；双阶段会增加模型调用成本。
- 没有训练开放式终极价值形成；当前只学习固定目标维度下的后果估计。
- 没有统一潜在社会世界模型；当前是来源分离的报告与粗粒度共享预测。
- 没有开放式技能程序发现；成功有限计划主要按带来源案例保留。
- 没有无限终身学习。网络、记忆池、历史、上下文、调用与行动都有上限。
- 神经更新不改变远程LLM权重，也不保证语言表达语义忠实于本地选择。表达阶段核对决策ID/结构而非由独立系统证明语义一致。
- 后果评价来自用户报告，可能偏置；“理解/任务/约束”维度不能消除所有迎合风险。草稿与对话重复评价同一结果也不是独立证据。
- 当前prequential比较在收到当前标签、训练它之前执行；延迟反馈之前模型可能已处理其他事件。因此它不是严格等同于“做动作那一瞬间”的效用误差。行动前的原始预测另行保存；观测预测有forecast_mse。
- UI已更新显示真实状态，但内部词汇预测、状态递推和冲突触发仍是有限代理，不能把字段名称当作心理属性。

## Replay与交付合同

模型输出保存为已记录的外生输入。复算实际重新执行其后状态、选择、梯度和工具，不重请求模型，不认证模型身份、原文真值或用户标签。源码hash/文件清单是本地完整性检查，不是第三方签名，也不是独立复核。

MANIFEST.sha256覆盖包内交付文件。ZIP本身的哈希与重新解压执行记录保存在ZIP之外，避免自引用。最终压缩包应与同名delivery_verification.json一起保留。

当前层：engineering implementation＋bounded offline mechanism-proxy experiments。主链：仅本包默认入口，用户EGO/ITL未接入。最高结论不超过指定trace/replay合同下的有界离线证据，不能升级为consciousness、emotion、subjectivity、agency、autonomy、Joi achieved或EGO readiness。
