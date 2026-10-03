# 本轮接入依赖修复（任务开始前）

首次身体启动 2026-10-03 15:08:14 UTC，子进程因缺少 canvas.node 退出 1；没有 login/spawn，也未发送四项任务。原始记录保留于本机 runs/p7/body_resume/1791040095140575900。主管进程退出 0 不能覆盖子进程失败。

定位到此前禁用 npm 生命周期脚本，遗漏了 canvas 及 gl 的原生组件。只执行已安装 prebuild-install 的下载/解包入口，显式指定官方 GitHub 发布 URL；不升级版本，不修改官方源码、适配器、任务提示或判据。

- canvas 3.2.3：https://github.com/Automattic/node-canvas/releases/download/v3.2.3/canvas-v3.2.3-napi-v7-win32-x64.tar.gz
  - canvas.node SHA256：f85e5b19198cc4800be76346bb2868abdd45acbb314968cf2fe41cb18b502bfa
- gl 8.1.6：https://github.com/stackgl/headless-gl/releases/download/v8.1.6/gl-v8.1.6-node-v127-win32-x64.tar.gz
  - webgl.node SHA256：6f7c73228bdf637bc4fc4a2f74d1eeb5042572d247a17b67e4bdd5f4a2fbb829

两次官方下载均 HTTP 200。之后完整 Agent 模块导入成功，官方 git diff HEAD 为空；视觉和生成代码仍关闭。本记录写定后只重试接入，时间盒和预算沿用 MC_CONNECTED_PRE_RUN.md。直接模块导入验证不等同于服务器登录成功。
