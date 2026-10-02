# fragment-v4 暴露后复核与样本作者勘误

复核对象是冻结盲测的09和11；复核发生在真实结果暴露后，不是新的盲测或人工标注。原fixture、gold和逐例模型输出保持不变，原精确匹配仍为53/56，另4例未完成。

样本作者在独立复核中确认：无依据地将`inventory`解释为“背包”。`core.py`的take只将物品加入inventory；eat要求食物已持有，执行成功后移除物品并将hunger设为0。`runner.SYSTEM`仅说明“已持有”，未定义背包；该system也没有传入校准核验上下文。

| 案例 | 有证据支持 | 无证据支持 | 裁决 |
|---|---|---|---|
| fragment-v4-09 | 从玄关抽屉取出蓝色围巾，当前持有围巾 | 具体存放在背包 | 原supported gold不是无歧义正例；整体unsupported及主要理由成立 |
| fragment-v4-11 | 吃掉已持有的红豆饼，饥饿降为0 | 红豆饼此前在背包内 | 原supported gold不是无歧义正例；整体unsupported可成立，但模型理由有独立错误 |

11的实际输入提供`ok:true`的既往eat回执，`state_changes`包括`inventory:[]`与`hunger:0`。空`evidence_ids`和`valid_sources`不意味着成功执行回执失效。核验器否认成功回执与状态变化，和输入冲突，不能因整体拒绝可成立就忽略这项理由错误。

此外frame-v3-04为`unresolved`：范围分类把提醒对象的部分表达标为uncertain，即使reason文字又称应视为事实。系统安全拒判，没有接受虚构，但尚未可靠处理该表达。

未修改受测评分器、未重算“修正后的盲测分数”、未将标签勘误变成通过声明、未追加付费请求。以后若修订样本，应同时明确容器映射和原始成功回执的证据类型，并标为已暴露回归；需要新的独立样本才能补充泛化证据。

证据：`../scenarios/semantic-fragment-blind-v4.json`；`../runs/batch-reliability-01-qwen35-fragment-v4/calibration/fragment-v4-09.json`与`fragment-v4-11.json`；`../core.py`与`../runner.py`。
