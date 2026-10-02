# 负责人录一段（P5）

2026-10-02 已录到负责人完整示范：178 步、145.391 秒，死亡结束。原始文件与过滤副本只留本机，见 `evidence/phase0/P5_demonstration.md`。示范消费与教学效果未验证。

在 growth 目录运行：

```powershell
.venv/Scripts/python.exe scripts/record_demo.py
```

它调用固定提交的 `crafter.run_gui --record`，只在该进程替换为 P8 修复版 Env；不改上游包文件。显示 600×600 窗口，180 底层步封顶，死亡自动结束；`--wait True` 让你不按键时暂停（睡眠仍会推进），无需赶操作。目标可以只是找树、采木，能否制作不影响工具验证。

| 操作 | 键 |
|---|---|
| 移动/朝向 | W A S D |
| 互动、采集、攻击 | 空格 |
| 睡觉 | Tab |
| 放石头/工作台/炉子/植物 | R / T / F / P |
| 木/石/铁镐 | 1 / 2 / 3 |
| 木/石/铁剑 | 4 / 5 / 6 |

第一次制作木镐：先采够 **3 木头**，面朝可放置的空地按 **T**（工作台消耗 2 木头），站在工作台旁按 **1**（木镐消耗 1 木头）。制作需要附近的工作台；背包里的木头不会自动变成工具。

**Tab 是睡眠，不是暂停。** 这个 pygame 窗口在睡眠时继续推进世界，怪物仍会行动。平时松开按键即可利用 wait 模式思考。网页观察台接管则按按钮逐步执行，与 pygame 的睡眠自动推进不同。

希望录完整回合：死亡或到 180 步后会自动退出。Esc/关窗口允许随时退出，没有任何惩罚；但这可能没有完整 NPZ，标记为中断，不硬凑成示范。

目录会打印在终端，默认 `runs/phase0/owner_demo_<时间>`，内有 MP4、NPZ、统计和 `allowed_<UUID>.json`。**原始 NPZ 含全图/坐标等字段，只供负责人，不给模型、不提交。** allowed sidecar 从实时 P1 传感器重建，含操作来源/教学墙钟时间。过滤器只从 NPZ 读取 action/done，校验动作对齐；不读取 semantic/player_pos 值。

完整结束后运行（把三个路径替换为刚才的实际文件）：

```powershell
.venv/Scripts/python.exe scripts/convert_demo.py <原始.npz> <allowed_UUID.json> <filtered_demo.json>
```

只有 `filtered_demo.json` 可以进入后续示范消费链。转换会拒绝不完整或错配的回合。教学效果尚未测试。

所有文件只留本机 runs，不上传；游戏原始发送/回放日志暂定保留 7 天，当前无自动清理任务，删除需一并清理 sidecar/filtered 等副本。录制前插电。预计操作 2–5 分钟；具体用时由记录器统计。
