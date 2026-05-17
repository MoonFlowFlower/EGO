---
name: python_debug
description: Python 报错、调试、最小复现和修复建议
tags: python,debug,code
---

# Python Debug Skill

使用步骤：

1. 先确认错误信息、运行命令、Python 版本、当前工作目录。
2. 优先给出最小复现和最小修复，不要大改架构。
3. 如果涉及文件/命令执行，必须先说明风险，再通过工具 gate。
4. 输出时包含：
   - 问题判断
   - 最可能原因
   - 最小修复
   - 验证命令
   - 如果仍失败下一步看什么
