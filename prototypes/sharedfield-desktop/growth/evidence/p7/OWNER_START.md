# P7 一页启动说明

**AIRI 文字聊天已接通；MC 尚未实测。** 本轮代理已关闭，重启会生成新令牌。U1 本批未通过，当前没有学习集成。记录见 `RESUME_REPORT.md`。

1. **启动本机代理。** 在 PowerShell 切到 `D:\Project\AIProject\MyProject\Ego_proejct_restart\.publish\EGO\prototypes\sharedfield-desktop\growth`，运行：

   ```powershell
   .\.venv\Scripts\python.exe -m p7.active_proxy --port 18787 --origin null --origin app://localhost --origin http://localhost
   ```

   在本地窗口输入云密钥，仅保留内存，不写进命令行或聊天。成功后使用 `http://127.0.0.1:18787/v1/`、新生成的本机会话令牌、模型 `ego-companion`。当前顺序为 DeepSeek V4.1 Flash/Wafer → 同模型/Together → Gemini 3.1 Flash-Lite/Vertex EU；只有输出开始前的指定传输错误可触发备用，并遵守冷却。这不是不限流保证；共用原 $5 账本，不重置未知预留。

2. **配置 AIRI。** 打开 `C:\Users\LEO\AppData\Local\Programs\airi\airi.exe`。到 Settings → Providers → Chat → OpenAI Compatible，使用实际提供方设置页，避免只填首次引导。

   **先把 Advanced 中 Base URL 改为上述回环地址，再填新本机令牌**；AIRI 会自动验证，不能在默认 OpenAI 地址下先填令牌。然后在思考/Consciousness 页面选择 OpenAI Compatible 和 `ego-companion`，打开 Chat。云密钥不交给 AIRI。本机令牌保存到 AIRI 配置已获授权，旧令牌在代理停止后失效。本次两次实际聊天已通过；本地语音未可用，识别、读屏、Analytics 保持关闭。

3. **打开目标世界。** 用 `D:\Software\MC\HMCL\HMCL.exe` 打开 Java 1.21.1，玩家名 Moonlight，在目标本机世界选择“对局域网开放”，记下 MC 显示的端口。当前实例没有已打开的世界；另发现的 `ServerFiles-7.2` 模组服务端存档不要直接用原版打开。已有世界或新建隔离测试世界仍待选择，未迁移存档。

4. **启动 Mindcraft 身体。** 世界已打开后，在同一 growth 目录运行：

   ```powershell
   .\.venv\Scripts\python.exe -m p7.start_body
   ```

   填 MC 显示的 LAN 端口，以及当前代理窗口里的**本机令牌**，点击 Start Mindcraft。此入口只接 127.0.0.1；默认端口 25575 只是待填示例。它拒收云密钥，不运行生成代码，也不打开网页控制口。此路径只完成离线验证，实际登录和玩法还未确认。进世界后由 Moonlight 的 MC 聊天与她交互；AIRI 聊天和身体尚未共享会话。

5. **验收和试玩。** 按原清单记录进入、跟随、砍树、木镐、停下的环境结果，不用回复文字替代。AIRI 自带 MC 因生成代码依赖暂停。具备可玩状态后由你亲自玩至少 15 分钟，再保存你的感受原话；当前没有体验记录。

先按身体窗口 **Stop Mindcraft** 或关闭窗口，再按代理窗口 **Stop** 或关闭代理。身体父进程退出会清理子进程，代理停止会撤销令牌。失败详情留在本机 `growth/runs/p7/body_resume/` 和 `growth/runs/p7/proxy/`，这些目录不提交。旧的 `p7.launch_proxy` / `runtime_session` 是历史冻结入口，不用于当前启动。
