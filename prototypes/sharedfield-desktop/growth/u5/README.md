# U5 只改记忆

在 `growth/` 使用 `.venv/Scripts/python.exe`。只有 D0、D1，无 D2。源库只读，七臂话语列表从 U3 S0 R 存档派生到 JSON；未改变生产记忆 API，也没有重新学习。新增程序话语用 `speaker=program`，正文以“（程序补充）”开头。

```powershell
.venv/Scripts/python.exe -m unittest u5.test_u5 -q
.venv/Scripts/python.exe -m u5.run freeze
.venv/Scripts/python.exe -m u5.run verify
.venv/Scripts/python.exe -m u5.run run --judge D0
.venv/Scripts/python.exe -m u5.run run --judge D1
.venv/Scripts/python.exe -m u5.report
.venv/Scripts/python.exe -m u5.audit
```

首次付费前提交并推送冻结清单、源码、全部输入及其哈希。D0 复用 N 72、R 63；补齐 R 9，新增五臂 360、F1b 82、噪声补测 30，共 481 请求。D1 七臂 504、F1b 82，共 586 请求。D0 噪声补测排在其余新决定之后；其余按冻结种子打乱。

单并发由运行锁及共享 DailyLedger 调用锁保证。配置、60 秒超时、一次同输入网络重试、两次连续无效停止沿用 U4。原始输出立即记录，导出每 10 条及退出时完成。`runs/u5/STOP` 可停止；一小时分段或当日预算恢复后以原命令加 `--resume` 继续，只处理没有完成输出的输入。开始标记无终止记录时停止，不盲重发。新配置或修正提示均不用于补救无效输出。

每天共用 $4 账本；U5 费用包含未知预留。每条调用后及下一条之前，按判断者、任务和记忆臂分别外推剩余费用；外推超过 $2 就停止请求，须负责人决定。无新结果的层用负责人原估计，不把 D0 的低费用外推到 D1。冻结后构造、阈值和输入不变。

判据见冻结清单与 `scoring.py`。重抽单位是每个人物内的测试时刻，20,000 次成对自助法，95% 区间，下限严格大于零。D5 关闭该判断者的解释；现象检查不成立时，C5/C1/C3 只报告。忙时开口包含普通回应；主动仅指问、问已知、建议。

原 S0 R 没有获知任何答案，各臂使用加分皆为零。作用域处理涉及 4 条负反应，F1b 使用材料提供的精确话题关联。只说明这批合成输入上的机制和连带，不说明她学会了什么。

首次启动在本地 60,000 字节检查处拒绝全反馈对照输入，发生在任何 request 事件、路由请求和付费之前。首版清单、源码和失败证据保留在 `evidence/u5/preflight_versions/v1/`，原运行目录留在 `runs/u5/preflight_v1_D0/`。v2 只将 U5 进程内的请求验收上限设为全批冻结请求的最大实际字节数 82,946；原始输入、顺序、模型和判据逐项一致。生产接口文件没有修改，字段验收、输出上限和费用规则全部保留。13 项离线检查及所有冻结请求的本地预验证通过。

D0 第 258 个新增请求因 `upstream_unavailable` 停止，没有收到输出。负责人明确授权“允许这条重试一次，再继续”，单独的 `OWNER_RETRY_ONCE.json` 在续跑前冻结并提交；`owner_resume.py` 只为该输入提供第 2 次尝试，其他请求仍走原运行器。重试成功，原失败和 $0.086888 未知预留保留。`OWNER_RETRY_RECHECK.json` 核对授权前 392 条决定、失败日志字节未变，两次请求相同且只有一个完成输出。该授权已消费，不能再用来恢复新的未知异常。

结果可用 `python -m u5.recheck --judge D0` / `D1` 独立复算：将四项差值分别映射到未修改的 `u3.statistics.comparisons`，逐一对照点估计、区间及严格正下限规则。

负责人随后授权“可以都重试一次”，覆盖当前 D1 中断及后续 `upstream_unavailable`。`OWNER_RETRY_POLICY.json` 冻结补充驱动、测试和原记录前缀哈希；`python -m u5.owner_retry_policy run` 续跑 D1，每条最多两次总尝试，不重放完成输出或不明中断。7 项离线边界检查通过，未知预留、外推 $2 和每日 $4 上限不变。若再次出现底层异常，仅新增异常类名和整数 errno 日志，不记录异常文本或请求凭证。一小时段限可自动续段，其他停止条件照旧。

负责人另明确“U5 按冻结配置继续，以后优先 OAuth”。已读到 OAuth 实时模型目录，但其中没有这批冻结的 DeepSeek；U5 不更换路线或判断者。

D1 在 566/586 处因单次请求保守预留闸门停止，下一条尚未发出。`RESERVATION_PROPOSAL.json`、`owner_reservation.py` 和 3 项独立测试备好一个待授权方案：单次预留门槛为 $2.05，原清单的全批外推停止线仍为 $2，每日仍为 $4。`run` 必须先有明确授权生成的 `OWNER_RESERVATION_LIMIT.json`，当前未授权。输入、重试次数和判分均不改。重试的完整字节/预留复核可运行 `python -m u5.recheck_retry_policy`。
