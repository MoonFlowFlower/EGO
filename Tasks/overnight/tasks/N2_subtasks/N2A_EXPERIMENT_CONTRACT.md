# N2A — 实验合同冻结

## 目标
在写脚手架和跑实验前，先冻结：
- 要验证什么
- 用什么输入序列
- 观测哪些字段
- 什么算通过
- 什么算失败
- 哪些结论绝不能越界

## 必做项
1. 明确至少 4 类必测对象：
   - identity continuity
   - cycle re-entry / strengthen
   - reflection trigger & revision impact
   - policy_hint / response_tendency 变化
2. 定义每类实验的：
   - 输入序列
   - 观测字段
   - 预期
   - 失败条件
3. 明确 artifact 输出位置
4. 明确哪些结论只能报 `partial`

## 成功判据
- 有结构化实验合同文档
- 后续子任务可以直接按合同执行
- 报告中已写清“不可宣称什么”

## 失败出口
若实验合同冻结不下来：
- 停在这里
- 不进入脚手架实现
- 报 `blocked` 或 `partial`
