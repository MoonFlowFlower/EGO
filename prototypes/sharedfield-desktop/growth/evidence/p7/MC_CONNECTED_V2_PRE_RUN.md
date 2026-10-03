# P7 接入适配 v2，任务前写定

2026-10-03 本轮第二次启动已 login/spawn，但 declare_recipes 原始包解析失败，因此先停机；未发出 follow/tree/pickaxe/stop。另用无模型、无聊天、无动作的 10 秒上限协议诊断连接捕获失败包后立即退出。未按“回复正常”掩盖错误。

根因是 minecraft-data 3.117.0 内 1.21.1 的配方序号保留了已不存在的 crafting_special_banneraddpattern，使 11 及后续编号错位。依据 Mojang 1.21.1 官方 server mappings（SHA1 03f8985492bda0afc0898465341eb0acef35f570）及本机 vanilla server-1.21.1.jar 中 RecipeSerializer/cze 的静态注册顺序确认。官方映射下载 URL：https://piston-data.mojang.com/v1/objects/03f8985492bda0afc0898465341eb0acef35f570/server.txt 。

仅在进程内修正这一张 1.21.1 配方编号表；不修改官方源码文件，不增加/替换游戏动作、提示或模型。原版离线重放同一 108271 字节包失败；修正后完整消耗 108271 字节，得到 1290 个配方。盔甲饰纹字段只是错位后的假象，探索过的饰纹字段修改已撤回，未进入接入版本。

补做此前遗漏的官方 postinstall（patch-package）：minecraft-data、mineflayer-pathfinder、mineflayer-pvp、prismarine-viewer、protodef 五个补丁应用；mineflayer 4.33.0 补丁与已安装 4.39.0 冲突，工具退出 1。保持已发布的 4.39.0 实现，不强行套旧补丁、不宣称完整原版安装。已核对旋转转换已在新版实现，挖掘水下和放置确认逻辑亦已变化。依赖状态作为本次组装变量记录，不能据此宣称无适配即用。

身体采用 mindcraft_body_v2.mjs / body_session_v2.py，保留原 v1 文件。唯一功能变化是模块导入前安装配方表修复；原有代码禁用、私有管道、Job Object、固定任务、取样不变。新版源文件、依赖文件和本预注册的哈希写入 MC_CONNECTED_V2_FREEZE.json 后重新接入。全部阈值、单次任务、预算与 15:34:30 UTC 截止仍沿用原预注册；若再出现协议错误，立即停止，不在本轮继续扩展协议修补。
