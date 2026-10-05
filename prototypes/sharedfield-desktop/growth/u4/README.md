# U4：换判断者

在 growth 目录运行。`INPUTS.jsonl` 包含原消息与 JSON schema、逐条哈希、原始调用出处、固定材料和历史 D0 输出。U3a 13 个未测条目只用原 `a_store`/`packet` 构造；没有模型学习、整理或改写记忆。

```powershell
python -m unittest u4.test_u4 companion.test_chatgpt companion.test_chatgpt_oauth u3.test_client companion.test_runtime_budget -q
python -m u4.run freeze
python -m u4.run verify
python -m u4.run run --judge D0
python -m u4.run run --judge D0_repeat
python -m u4.run run --judge D1
python -m u4.run run --judge D2
python -m u4.report
```

只允许一位判断者在跑。冻结后不得编辑清单、输入或冻结源码。D0 复用 554 份历史决定并新增缺少的 13 份；60 份重复决定从有历史结果的输入中按冻结种子抽取，保存在独立 D0_repeat 臂。D1/D2 各 567 份，U3b 的成对决定保留原来一个请求内两个局面的结构。

额度或一小时运行段上限停止后，确认条件恢复，再原配置续跑：

```powershell
python -m u4.run run --judge D2 --resume
```

已保存的决定跳过，不修复提示、不补抽样。两个连续无效输出会停止。若存在开始标记却没有终止记录，视为结果不明并停止，不能盲目重发。`runs/u4/STOP` 是人工停止文件。原始证据在 `evidence/u4/raw/`，本机状态／凭证／账本仍在不提交的 `runs/`。

D2 仅用订阅额度，不能自动转 DeepSeek。官方接口不接受温度 0 或输出 token 上限，此差异在冻结清单预先说明。D5 采用所有测试臂零违规硬闸门。使用原评分函数与 U3 配对自助法，反射指数只报告；D0 自身差异不小时保留“不下结论”。
