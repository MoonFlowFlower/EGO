# Shared Field v0.5 — 项目入口

## 目标不变
共同经历、持续自我模型、情感样调节、学习、内生目标、社会理解和可测行动。可以直接测试“感觉/想法/意愿”；不要改回任务助手、人格prompt或定时陪聊。

## 当前实际路径
`run.py shared → SharedService → SharedCore → Mind / World / continuity`；语言连接复用原 Provider，表达前固定快照与已选意图。用户按钮或有来源请求进入持续共同承诺，影响下一动作；预测器从唯一移动选择更新，影响同行排序。权限仅限内置环境。

## 六项状态
层级：engineering implementation + bounded learning/adaptation and mechanism hypotheses。
主链接入：本压缩包默认 shared 入口已接通；用户 EGO/ITL 仓库未知、未修改。
启用：启动/恢复暂停；本地报告默认，API由用户选择；同行约定不授予步骤。
实际触发：本轮真实本地HTTP、状态读写、等待、学习、言行回执、检查点接续有测试；新版真实模型语义与Windows运行未知。
结论上限：bounded offline mechanism evidence under a specified environment/trace/replay contract。
下一最小闭环：接续真实会话，验证表达/实际意图/后续执行一致；共同约定可维持、解除；真实模型的语言修复命中与误修正均记录。

## 代码
world.py：物理世界与公共观测；mind.py：概率学习、评价、目标与可靠路径。
continuity.py：承诺、伙伴选择预测、未决问题、来源记忆。
grounding.py：已选意图与有限语言冲突修正，不是语义真值判定器。
core.py：事件、快照、复算与接续；evidence.py：JSON便携数值合同；migration.py：冻结v4验证。
service.py/http.py/web：真实主入口、暂停、有限授权、异步语言、导入导出。

## 先验、学习与未完成
固定先验：评价映射、初始价值、4类表示、动作语法、同行与等待规则、权重。
实际学习：物理后验、能力校准、类型收益、选择预测器的在线梯度。
来源整理：经历问题与检查摘要，不能算新证据或神经巩固。
未实现：开放式终极价值、通用社会潜变量、终身神经可塑性、视觉/语音/真实电脑控制。

## 证据与负结果
本轮266项工程测试通过（最终解压另有独立交付记录），不代表机制优越性。原固定效用8种子×5方法中full平均 -1.539，flat 0.149；没有为翻绿调阈值。小型伙伴预测实验可被频次统计同样解释。强长上下文/元学习基线缺失。保留负结果、不要继续加一个情绪字段包装成功。

读 README.md、docs/continuity/DESIGN.md、VALIDATION.md 后再改代码。真实用户导出不在通用压缩包内。
