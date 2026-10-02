# SharedField 桌宠与记忆实验源码快照

按用户“推送到 MoonFlowFlower/EGO、新建分支”的明确授权，于 2026-10-01 从 `Ego_proejct_restart` 导入。此目录独立保存当前桌宠原型、SharedField 源码、memory_lab 实验实现及项目任务板；不改变仓库根目录的产品路线、入口或默认运行配置。

## 内容与边界

- `desktop_pet/`：小屋、便签编辑与回信、生活动作、事实与虚构分区的生活分享。
- `desktop_pet_assets/`：原创临时素材。
- `memory_lab/`：隔离记忆实验、场景、依赖锁、上游许可与分析文档。正式对照和成长效果尚未验证通过；不要将历史诊断视为通过证明。
- `SharedField/`：现有源码、示例及文档。
- `TASK_BOARD.md`：本地项目的工作记录，不是仓库根目录主线的路由指令。
- `SOURCE_MANIFEST.json`：本次复制文件的 SHA-256，可核对原始源码字节。

这是源码快照，不是包含私人数据的完整安装备份。未上传个人存档、API 密钥、虚拟环境、缓存、实验运行数据库、原始调用记录、日志、历史 ZIP 包和机器专用启动器。历史报告中引用的这些本机材料可能不在此快照中；依赖历史 ZIP 的兼容性验证也需要另行恢复原始材料。实验预算账本未发布，不能在新机器上重新初始化账本并将它当作原活动的继续。

## 本地启动前准备

在此目录执行开发检查：

```powershell
python -B -m unittest discover -s desktop_pet/tests -v
```

准备完整显示资源和本地模型配置后，可从此目录执行 `python -B -m desktop_pet.server`，打开 `http://127.0.0.1:18180`。启动说明见 `desktop_pet/README.md`。

悠小喵 Live2D 包的许可禁止再分发，因此 `desktop_pet/local_assets/` 未上传。请通过合法渠道取得资源，在本机按原目录布局导入。Cubism Core 缓存也未上传；请按其官方许可自行取得，版本来源及校验值见 `desktop_pet/web/vendor/lock.json`。已保留 PixiJS 与 pixi-live2d-display 的许可文件。

模型配置目前仍保留原源码中的机器路径，凭据读取入口见 `memory_lab/provider.py`。新机器需自行配置本地凭据位置，绝不能把密钥加入版本控制。本次发布没有发起模型调用、重开实验或更改已有相处数据。
