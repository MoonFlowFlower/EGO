# P7 一页恢复与启动说明

**当前尚不能一起玩。** AIRI 已安装，代理与固定配置已保存；模型路由失效，AIRI 聊天配置未贯通，Mindcraft 启动入口未交付。此页记录恢复顺序，不能当成一次成功演示。负责人 15 分钟试玩及感受原话仍待完成。

1. **先恢复固定模型路线。** 在任何新付费试验前写清新一轮固定配置及停止规则，保持 ZDR、禁止回退、原 $5 共享账本。当前旧路线的新鲜预检会拒绝；不要删账本、释放未知预留或绕过预检。
2. **启动本机代理。** 在 PowerShell 切到 `D:\Project\AIProject\MyProject\Ego_proejct_restart\.publish\EGO\prototypes\sharedfield-desktop\growth`，运行下方命令。本地窗口输入上游密钥，仅留内存；不把密钥放在命令行或聊天里。

   ```powershell
   .\.venv\Scripts\python.exe -m p7.launch_proxy --port 18787 --origin null --origin app://localhost --origin http://localhost
   ```

   窗口若显示 `Startup refused: route_preflight_rejected`，停在这里。成功后 Base URL 是 `http://127.0.0.1:18787/v1/`。每次重启令牌都会变化，旧令牌失效。
3. **启动 AIRI。** 打开 `C:\Users\LEO\AppData\Local\Programs\airi\airi.exe`。选择 OpenAI Compatible，只填上述地址和本机代理令牌；不填云端密钥。当前 v0.12.0-beta.5 引导 Ping 后实际聊天仍缺少 provider credentials，须先解决配置保存链路，再以原固定聊天探针复验。保持 Analytics、识别与读屏关闭；Kokoro 声音尚不可用。不要注册/登录账号来绕过这个问题。
4. **确定世界。** 用 `D:\Software\MC\HMCL\HMCL.exe` 打开 Java 1.21.1，玩家 Moonlight。这个实例目前没有现有存档；待确认新建隔离 P7 世界，或由你打开另一个已有 1.21.1 世界并对局域网开放。目标本机 `127.0.0.1:25575`。不连公共服务器，不升级旧世界。
5. **身体与试玩。** AIRI MC 因必须执行生成 JavaScript 暂停。Mindcraft 的 `p7/mindcraft_settings.json` 和 `mindcraft_profile.json` 是待验证配置；先完成控制口与进程清理的工程处理，再提供启动入口。随后按清单测进世界、跟随、砍树、木镐、停下，记录真实位置/背包/动作，不用文字回复代替。具备可玩状态后请你亲自玩至少 15 分钟，再保留你的感受原话；现在没有体验记录。

停止代理使用窗口 **Stop** 或关闭窗口；它会撤销本次令牌。完整记录在本机 `growth/runs/p7/`，不提交。报告见 `REPORT.md`；此阶段不接 U1 学习，也不声称她已经学会你。
