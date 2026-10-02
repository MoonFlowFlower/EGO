# Reading Loop Implementation Plan

**Goal:** 让一次有来源的共同阅读，经用户纠正产生可持续的方法，并在新材料上可比较。
**Architecture:** reading reducer 使用 MemoryStore.notes 持久化活动对象；独立 service mixin 接现有 worker/provider；同源网页接现有鉴权。旧版迁移使用冻结验证器。
**Tech Stack:** Python标准库、SQLite、原生HTML/JS。
**Spec:** ../specs/2026-09-23-reading-loop.md

Global constraints: Python >=3.10；无新增运行依赖；不写密钥；原文24000字符；重启暂停；没有模型即不能生成虚假成果。开发在独立解压副本，不改原 ZIP。

Review focus: 取消/暂停期间迟到结果；相同材料重复冒充迁移；纠正与方案泄漏到基线；长输入超限；删除后阅读/方法或迁移归档复现。

## Task 1: 持久活动与学习合同
- [x] 测试导入、段落引用、纠正→方法采纳→不同材料两臂比较、评分来源、删除和恢复；新增 tests/test_reading.py。
- [x] 运行 `python -m unittest tests.test_reading -v`，确认缺少 reading 操作而失败。
- [x] 新增 switchlab/memory/reading.py，接口 `reduce(store,payload,at,eid,seq)`、`view(store)`、`next_job(store)`、`build_request(store,job)`；MemoryStore._reduce 将 kind=reading 分派；保存于 notes。
- [x] 跑同一测试，检查活动、方法和学习冻结的可见行为。

## Task 2: 真正调用、界面与接续
- [x] 新增 service/HTTP/pause/manual/同源测试，确认旧入口不支持完整阅读而失败。
- [x] reading_service.py mixin 提供 reading_command / reading_run_once；现有 run_once 优先处理已请求阅读；既有模型连接/调用预算/手动交换复用。
- [x] /reading 页面实际文本上传、成果、纠正、采纳、转移、盲评、状态恢复；主聊天有入口和活动上下文。
- [x] 指纹使用规范路径；新增显式 frozen v0.6 migration 与原存档验证测试。

## Task 3: 验收与真实活动
- [x] 跑 `python run.py test --out evidence_v07/tests`，处理相关失败，保留未解决失败。
- [x] 浏览器真实点击完整流程；人工模型夹具只认证界面工程链。
- [ ] 读取用户指定 codex key，仅进程内使用；真实模型阅读用户给出的需求材料，展示成果并收集用户纠正。新材料两臂对照保留真实结果，缺少评分就保持待评。
- [x] 更新 README/PROJECT/验证报告、manifest，保留完整证据与运行入口。

Execution: 本会话直接执行，遵循当前开发者指令在已授权范围持续推进，不把已批准范围重复转为批准门槛。非 Git 解压包使用只读原副本与新目录做差异依据。最终单独审查与工程验收并行。

当前：工程实现、完整回归、浏览器夹具流程、实际模型阅读与用户纠正重读、重启迁移已完成。真实方法采纳与新材料评分等待用户选择，不能标为全部目标达成。独立review的7项问题与最后采纳来源删除问题均已修复；当前正式运行目录user_data/reading_v07_final。
