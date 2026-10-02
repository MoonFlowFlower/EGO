# Shared Field v0.5 — 实际验证与限制

## 当前范围
工程实现、有限学习适应与机制假设；本压缩包默认 shared 入口使用新增路径。启动/恢复暂停，用户授予有限步数后才行动，API另行启用。未修改用户 EGO/ITL 仓库、Codex 会话或真实电脑。

## 本轮读回的实际结果
| 检查 | 结果与范围 | 记录 |
|---|---|---|
| 修改前完整回归 | 225项通过 | evidence_v05/baseline_tests/ |
| 最终完整测试 | **266项通过，零失败、错误、跳过** | evidence_v05/final_tests/，final_tests.log |
| 用户v4导出 | 冻结原代码重算108条，原哈希匹配，物理步26 | user_replay_audit.json；独立输出trace_review |
| 真实应用HTTP导入接续 | 导入原v4，暂停，导出v5复算，再实际执行26→27 | 独立输出 user_continuation_test.json；交付重解压另测 |
| 浏览器界面 | **25项通过，零JS异常**，含同行/等待/恢复、回执、导出复算、导入归档、390px布局 | evidence_v05/browser/result.json |
| 实际HTTP与权限 | Host/Origin/token、非对象与真实大小导入、路径隔离；Provider的HTTP测试端点 | tests/test_shared*_http.py、test_shared_pipeline.py |
| 同历史干预 | 两条构造经历改变同一目的地选择；冻结/独立模式消除差异；简单频次baseline可复制 | evidence_v05/continuity_probe/ |
| 等待 | 100次轮询无新增事件，无物理动作、无语言调用，保留8步授权 | 同上 |
| 原固定效用比较 | 8世界×5方法，至多80步，未变评价公式；full均值-1.539，flat 0.149 | evidence_v05/benchmark/ |
| 语法 | 当前运行Python文件通过3.10 grammar parse，app.js通过node检查 | evidence_v05/python310_syntax.json |

实际执行环境 Linux / Python3.13.5。其他Python版本与Windows没有实机测试。UI中的语言为明确TEST_FIXTURE；本轮没有请求真实云模型或运行本地LLM。用户提供的v4真实运行文本用于诊断，不等于v5的真实模型语义测试。

## 原始导出的严格复算失败不能隐藏
v4原样reader对用户导出在 E000005 失败，原因是浏览器JSON序列化使0.0变0。新路径不是删除来源哈希，而是用固定SHA校验的原版运行代码逐事件重算，按原12位浮点合同兼容整数/浮点表示，布尔值保持区别；**原hash/state_sha256/head字符串仍必须匹配**。报告 strict_original_reader_used=false。这只是完整性与计算复算，不认证历史确实来自某台电脑或某个云模型。

v5使用独立、有限数字规范化合同。旧记录作为显式origin保留，事件ID接续；新模块从零初始化，旧未完成付费问题不自动重试。原物理学习不重复训练、不重写旧错误。通用zip不包含真实用户的完整导出或接续文件。

## 浏览器边界
本轮再次实际尝试原生Chromium访问loopback，返回 ERR_BLOCKED_BY_ADMINISTRATOR，记录在 native_browser_attempt.json；没有绕过策略。HTML/CSS/JS通过明确进程内测试传输调用真实Service，真实HTTP另测。**不验证原生浏览器网络或CSP端到端执行**。

最初界面测试使用不存在的CSS选择器而超时；修正测试选择器后重跑，产品行为未为之改动。历史失败文件保留，但最终采用 browser/result.json。主截图是实际界面与合成/本地测试内容，不伪装成真实LLM表现。

## 机制与表达限制
- 已选意图、备选、已执行结果和修订分开；某些近未来动作冲突会被局部校正。有限措辞守卫不认证全部语义，可能漏掉新说法，也可能误修正；原始输出保留。
- 同行/等待约束、评价规则、初始价值与选择权重是工程先验，不是学出了自主性或真实情感。
- 伙伴模型学习的是有偏的4类选择倾向；可达性、重复测试等是替代解释。频次记忆可复制本次合成结果，不声称统一社会模型。
- 经历脉络与回看是来源整理，不产生新证据或神经巩固。旧小神经网络不是默认情感核心。
- 新输入/暂停仍能取消旧请求。物理玩家动作、会合邀请、同行/等待不会抹掉问题；期间变化由较早快照标签披露，旧回答不能回滚或执行旧计划。
- 原效用比较仍不支持完整候选更有效；不能为同一低头部空间基准不断调阈值。当前新增价值主要待实际共同活动检验，强长上下文、跨episode元学习baseline仍缺失。

## 工程复核
由同一实现者自查，没有独立审计者。红绿记录覆盖目标归属、异步回复、数值导出、同伴问题归属、会合完成、非对象/大导入、提问主体误校正等；旧测试中“地图动作必须丢弃回复”明确更换为新的合同，暂停取消测试保留。

源码指纹与MANIFEST是完整性检查，不是外部签名。最终ZIP的解压、全清单、完整测试、复算与继续运行由包外 SharedField_v0.5_delivery_verification.json 记录，避免zip哈希循环写入自身。

最高允许描述：bounded offline mechanism evidence under a specified environment/trace/replay contract。没有意识、真实情绪、真实自主、电子生命或EGO readiness结论；没有真实电脑/Jev/语音、新云服务或权限扩张。
