# Mindcraft 首次启动前固定配置

官方 v0.1.4，提交 `b36eaf7e61b3f6bd031fdb531812b2e3c42b6c73`。源码不修改，使用官方 `SETTINGS_JSON` 和 profile 接口。代理名 `EgoP7`，跟随对象 `Moonlight`，Minecraft 1.21.1，本机 `127.0.0.1:25575`。当前世界尚待负责人确认。

- `allow_insecure_coding=false`，另封锁 `!newAction`；清除启动环境里的 `INSECURE_CODING`（官方代码连字符串 false 都会按开启处理）。不注册/注入新的模型动作。
- 保留官方 assistant profile 的提示词/技能；temperature=0、输出上限1024、单轮最多8个连续命令。不能通过改任务提示或追加提示把失败重算通过。
- 聊天、code_model/vision_model 的继承地址均是本机代理；视觉/浏览器viewer/语音关闭。无初始化自动模型消息。
- `language=en` 让官方翻译函数直接返回原文；原始中文任务仍交给固定模型。否则官方 `google-translate-api-x` 会额外外发聊天，违反本轮内容路径限制。
- 显式 embedding 指向同一代理；代理不提供 `/embeddings`，预期本机404后官方代码转词重叠检索。不允许省略embedding而隐式转向OpenAI公网默认地址。404只算本地降级记录，不算云模型失败。
- 本机代理令牌仅以子进程环境传入；无 keys.json，不传云密钥。stdout/stderr去除已知令牌后只写本机 runs。官方组件自身产生的 bot history 留在仓库外，报告说明该额外本地副本。
- MindServer只监听localhost:18080，记录其官方 `state-update` 的位置、动作与背包。任务提示通过官方 `send-message` 接口，以 Moonlight 为目标玩家；自动化发出的命令另标明 `operator=codex_fixture`，不冒充负责人试玩。
- 预先写定的进世界/跟随/原木/木镐/停止判据仍在 CHECKLIST.md。进入世界后先记录初始条件。原木和木镐须同起点副本；无法实现时单列环境差异，不称公平比较。
- AIRI 自带 Minecraft 身体因生成 JavaScript 执行无法独立关闭而停止。Mindcraft 没有自动接通 AIRI 的聊天状态；除非实际验证共享上下文，否则明确报告分离。

## 启动前检查后的状态（追加，不修改上述判据）

未启动。世界仍待确认，固定模型路线已预检拒绝；只读复核另发现控制口可改安全设置、监督器异常退出清理不足。未运行草稿已保留到忽略的 runs，未作为可执行入口提交；细节见 `MINDCRAFT_REVIEW.md`。不能把以上计划动作描述当成已发生的运行。
