# N4B — 只读诊断入口或等价脚本

## 目标
给用户或操作员一个无需深入源码即可查看关键状态的只读入口。

## 至少应能看到
- 最近 trace 关键字段
- cycle hit / cycle id
- reflection_trigger
- revision_counter 变化

## 成功判据
- 存在只读诊断入口或等价脚本
- 有实际输出示例
- 不越权写状态
