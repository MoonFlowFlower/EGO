# Mindcraft 启动前只读复核

检查对象：官方 v0.1.4、提交 `b36eaf7e61b3f6bd031fdb531812b2e3c42b6c73`；仓库外 checkout 干净，未改第三方源码。静态检查不等于真实连接或玩法验收。

## 确认的初始配置

- `allow_insecure_coding=false` 和 `!newAction` 黑名单阻断生成代码动作；`INSECURE_CODING` 环境变量必须删除，不能设成字符串 `false`。
- `language=en` 令双向翻译函数直接返回原文，中文聊天不会再经过 Google 翻译。
- `allow_vision=false` 不创建 Camera，观察方法直接拒绝；`render_bot_view=false`、`speak=false`。
- 显式 embedding 对象的 URL 经 `selectAPI/createModel` 传到 GPT 客户端。当前代理没有 `/embeddings`，预期本机错误后转词重叠检索；没有外部地址回退。不要省略或清空 embedding，那会触发默认 OpenAI 客户端。见官方 `src/models/prompter.js:78`。
- 当前不存在 `keys.json`；官方文件凭据优先于环境变量，后续启动必须拒绝它覆盖本机令牌。profile/settings 不含密钥。
- 官方会把本地聊天历史写到仓库外 `bots/EgoP7/`，`log_all_prompts=false` 不会关闭这些历史。本轮没有启动 agent，因此没有实际 MC 聊天历史或决定记录。

## 启动前发现的问题及处理

1. 官方 `src/mindcraft/mindserver.js` 的 `create-agent` 和 `set-agent-settings`（约第150行）没有鉴权；后者可替换设置并重启代理。虽然只绑定 localhost，但 `new Server(server)` 没有 Origin 白名单或认证。配置、设置规格和入口中未找到关闭这些控制事件的现成选项。MC 的 `auth: offline` 不是控制口鉴权。当前配置不能保证开关在运行期间一直不被控制口改动；没有发生攻击的证据。
2. 本轮未运行的监督器草稿只覆盖正常退出。启动后的异常、信号或输出错误可能留下主进程及其子进程。正常 MindServer 断连已有官方 `cleanKill`，不能把正常关闭也说成必然泄漏。后续应使用统一清理和本轮进程树的 Windows Job Object 约束。

基于低成本摸底的范围，本轮不扩建控制层；先保留官方配置检查结果，不交付这个草稿作为可运行入口。草稿原样移入忽略的 `runs/p7/drafts/mindcraft_runner.unlaunched.mjs`，SHA-256 `de5bf4922347695a107c2f0f45b1e867e69362eb9bc44953b85251ec04bef7d5`。只做过语法检查，没有执行官方 main.js、连接世界或发送任务。

后续最小工程工作是限制控制连接/危险设置变更，并约束子进程全生命周期；仅关闭网页 UI、修改 CORS 响应头或换端口不足。完成后仍需按原判据实际测试，不能把静态复核改记为进世界、跟随或停下通过。
