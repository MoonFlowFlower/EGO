# P7 一页启动说明

**已完成超过 15 分钟的负责人试玩；Mindcraft 能完成部分短任务，持续任务和合成恢复仍有故障，完整玩法验收未通过。** 最近一轮提前断开，身体和代理现已停止，退出原因未确认。重启代理会生成新令牌。U1 本批未通过，当前没有学习集成。最新体验与诊断见 `MC_OWNER_TRIAL_REPORT.md`，原固定任务见 `MC_CONNECTED_REPORT.md`，此前聊天与语音记录见 `RESUME_REPORT.md`。

1. **启动本机代理。** 在 PowerShell 切到 `D:\Project\AIProject\MyProject\Ego_proejct_restart\.publish\EGO\prototypes\sharedfield-desktop\growth`，运行：

   ```powershell
   .\.venv\Scripts\python.exe -m p7.active_proxy --port 18787 --origin null --origin app://localhost --origin http://localhost
   ```

   在本地窗口输入云密钥，仅保留内存，不写进命令行或聊天。成功后使用 `http://127.0.0.1:18787/v1/`、新生成的本机会话令牌、模型 `ego-companion`。当前顺序为 DeepSeek V4.1 Flash/Wafer → 同模型/Together → Gemini 3.1 Flash-Lite/Vertex EU；只有输出开始前的指定传输错误可触发备用，并遵守冷却。这不是不限流保证；共用原 $5 账本，不重置未知预留。

2. **配置 AIRI。** 打开 `C:\Users\LEO\AppData\Local\Programs\airi\airi.exe`。到 Settings → Providers → Chat → OpenAI Compatible，使用实际提供方设置页，避免只填首次引导。

   **先把 Advanced 中 Base URL 改为上述回环地址，再填新本机令牌**；AIRI 会自动验证，不能在默认 OpenAI 地址下先填令牌。然后在思考/Consciousness 页面选择 OpenAI Compatible 和 `ego-companion`，打开 Chat。云密钥不交给 AIRI。本机令牌保存到 AIRI 配置已获授权，旧令牌在代理停止后失效。本次两次实际聊天已通过；本地语音未可用，识别、读屏、Analytics 保持关闭。

3. **打开目标世界。** 负责人已启动独立的 Java 1.21.1 服务器，并用 Moonlight 进入，地址 **127.0.0.1:25565**。客户端仍通过 `D:\Software\MC\HMCL\HMCL.exe` 启动；此连接方式不需要再点“对局域网开放”。若以后改用单人 LAN 世界，则填写当次显示的端口。现有世界未迁移、重置或替换。

4. **启动 Mindcraft 身体。** 世界已打开后，在同一 growth 目录运行：

   ```powershell
   .\.venv\Scripts\python.exe -m p7.start_body_v2
   ```

   保持默认端口 25565，填当前代理窗口里的**本机令牌**，点击 Start Mindcraft。此入口只接 127.0.0.1，拒收云密钥，禁止生成代码，不打开网页控制口。v2 包含已复核的 1.21.1 配方编号兼容修复；旧入口保留为历史冻结版本，勿继续用于当前实测。新 GUI 已做语法检查，实际 MC 通过同一个 v2 主管和身体的私有管道启动；本轮没有重新验证 GUI 点击启动。

   进世界后，Moonlight 要先来到机器人附近，再用 MC 聊天与它交互。它无法从未加载的玩家实体推断你的位置；最近退出位置约 (6.46,109,-53.41)，以后以真实登录日志为准。AIRI 聊天和身体尚未共享会话。

5. **验收和试玩。** 按原清单记录进入、跟随、砍树、木镐、停下的环境结果，不用回复文字替代。AIRI 自带 MC 因生成代码依赖暂停。2026-10-03 已有 16 分 38 秒的真人消息跨度和 6 张截图，原话与截图仅在本机 runs。这条只作体验记录，不覆盖原固定任务结果。当前库存显示会包含合成格材料，反复合成失败时先停止身体并保留日志；不能用模型的完成宣称确认物品或建房完成。

先按身体窗口 **Stop Mindcraft** 或关闭窗口，再按代理窗口 **Stop** 或关闭代理。身体父进程退出会清理子进程，代理停止会撤销令牌。失败详情留在本机 `growth/runs/p7/body_connected_v2/`、旧 `body_resume/` 和 `proxy/`，这些目录不提交。旧的 `p7.launch_proxy` / `runtime_session` 是历史冻结入口，不单独用于当前启动。`p7.connected_proxy` 专用于本次已写定的额外 $0.50 时间盒，不是重置预算的入口。
