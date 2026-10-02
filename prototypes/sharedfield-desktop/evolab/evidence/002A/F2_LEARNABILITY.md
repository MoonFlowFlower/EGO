# EVOLAB-002A F2 可学性闸门 L

状态：STOP_L_EXHAUSTED；选定级：None。

累计GPU任务墙钟 20744.725 秒（含CPU调度、CUDA同步、检查点、评估和重测W）。预算21600秒。

完整400代预跑：285.3970934999961 秒；四级规模规划估计：20548.59073199972 秒。

固定毒性0.15。L0移动额外耗能0；L1累加7×7视野；L2累加σ=0.05、种群512；L3累加初始能量1.0。每级2臂×2世界×3种子，最终512个pilot开发回合。

域pilot_train=420000、pilot_dev=430000，master_seed=20261002。两臂配对种子0–2，初始化与突变也含pilot域。每20代128固定开发回合仅用于日志；最终512回合generation标签1，与中途标签0隔离。没有保留集访问。

首轮B/drift/seed0预先指定跑满400代实测；其他试跑在连续20代零标准差时允许提前结束并取该时刻均值。collapsed_at为第20代检测时刻。未用最佳检查点。标准差以float64计算，避免常数float32向量因归约舍入出现伪非零。适应度、OpenES秩和Adam均沿用001A。

## L0

配置：`configs/002a_pilot_L0.yaml`。

| arm | world | seed | generations | collapsed_at | S | ate good ≥1 | survived first | good/bad mean | seconds |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|
| gru_mb_plastic | drift | 0 | 400 | None | 0.105351562 | 0.121093750 | 0.042968750 | 0.269531/0.347656 | 285.397 |
| gru_fixed | static | 0 | 341 | 341 | 0.101710938 | 0.003906250 | 0.000000000 | 0.076172/0.005859 | 68.609 |
| gru_fixed | static | 1 | 400 | None | 0.192437500 | 0.455078125 | 0.000000000 | 2.427734/0.619141 | 212.558 |
| gru_fixed | static | 2 | 400 | None | 0.127958333 | 0.261718750 | 0.000000000 | 0.765625/0.353516 | 178.515 |
| gru_fixed | drift | 0 | 400 | None | 0.101713542 | 0.050781250 | 0.025390625 | 0.148438/0.169922 | 109.326 |
| gru_fixed | drift | 1 | 400 | None | 0.100186198 | 0.003906250 | 0.003906250 | 0.011719/0.017578 | 94.759 |
| gru_fixed | drift | 2 | 400 | None | 0.101450521 | 0.027343750 | 0.009765625 | 0.058594/0.060547 | 101.503 |
| gru_mb_plastic | static | 0 | 400 | None | 0.123075521 | 0.263671875 | 0.000000000 | 0.615234/0.298828 | 232.658 |
| gru_mb_plastic | static | 1 | 400 | None | 0.104617188 | 0.078125000 | 0.000000000 | 0.160156/0.072266 | 261.189 |
| gru_mb_plastic | static | 2 | 400 | None | 0.188792969 | 0.519531250 | 0.000000000 | 2.107422/0.443359 | 677.485 |
| gru_mb_plastic | drift | 1 | 400 | None | 0.100052083 | 0.003906250 | 0.000000000 | 0.005859/0.009766 | 275.254 |
| gru_mb_plastic | drift | 2 | 400 | None | 0.101894531 | 0.027343750 | 0.013671875 | 0.093750/0.050781 | 275.037 |

| arm | world | seed-average S | ate good ≥1 | survived first | absolute gate |
|---|---|---:|---:|---:|---|
| gru_fixed | static | 0.140702257 | 0.240234375 | 0.000000000 | {'complete': True, 'ate_good': False, 'survival': False} |
| gru_fixed | drift | 0.101116753 | 0.027343750 | 0.013020833 | {'complete': True, 'ate_good': False, 'survived_first': False} |
| gru_mb_plastic | static | 0.138828559 | 0.287109375 | 0.000000000 | {'complete': True, 'ate_good': False, 'survival': False} |
| gru_mb_plastic | drift | 0.102432726 | 0.050781250 | 0.018880208 | {'complete': True, 'ate_good': False, 'survived_first': False} |

L0通过：False。

W沿用F1：L0世界一致，L1视野和L2 ES改动不影响拥有全坐标的脚本基线，轨迹不变。

## L1

配置：`configs/002a_pilot_L1.yaml`。

| arm | world | seed | generations | collapsed_at | S | ate good ≥1 | survived first | good/bad mean | seconds |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|
| gru_mb_plastic | drift | 0 | 330 | 330 | 0.100098958 | 0.003906250 | 0.000000000 | 0.003906/0.003906 | 109.961 |
| gru_fixed | static | 0 | 400 | None | 0.148946615 | 0.320312500 | 0.000000000 | 1.265625/0.462891 | 211.261 |
| gru_fixed | static | 1 | 400 | None | 0.120638021 | 0.179687500 | 0.000000000 | 0.683594/0.363281 | 203.858 |
| gru_fixed | static | 2 | 400 | None | 0.111091146 | 0.085937500 | 0.000000000 | 0.369141/0.189453 | 159.397 |
| gru_fixed | drift | 0 | 400 | None | 0.100372396 | 0.056640625 | 0.021484375 | 0.119141/0.250000 | 128.498 |
| gru_fixed | drift | 1 | 400 | None | 0.101936198 | 0.058593750 | 0.019531250 | 0.125000/0.181641 | 128.984 |
| gru_fixed | drift | 2 | 400 | None | 0.101936198 | 0.025390625 | 0.011718750 | 0.076172/0.066406 | 101.126 |
| gru_mb_plastic | static | 0 | 400 | None | 0.163520833 | 0.324218750 | 0.000000000 | 1.623047/0.359375 | 424.400 |
| gru_mb_plastic | static | 1 | 400 | None | 0.154602865 | 0.326171875 | 0.000000000 | 1.431641/0.296875 | 415.369 |
| gru_mb_plastic | static | 2 | 400 | None | 0.117373698 | 0.265625000 | 0.000000000 | 0.517578/0.371094 | 377.832 |
| gru_mb_plastic | drift | 1 | 373 | 373 | 0.100147135 | 0.003906250 | 0.000000000 | 0.003906/0.001953 | 125.057 |
| gru_mb_plastic | drift | 2 | 400 | None | 0.102315104 | 0.054687500 | 0.027343750 | 0.136719/0.191406 | 221.832 |

| arm | world | seed-average S | ate good ≥1 | survived first | absolute gate |
|---|---|---:|---:|---:|---|
| gru_fixed | static | 0.126891927 | 0.195312500 | 0.000000000 | {'complete': True, 'ate_good': False, 'survival': False} |
| gru_fixed | drift | 0.101414931 | 0.046875000 | 0.017578125 | {'complete': True, 'ate_good': False, 'survived_first': False} |
| gru_mb_plastic | static | 0.145165799 | 0.305338542 | 0.000000000 | {'complete': True, 'ate_good': False, 'survival': False} |
| gru_mb_plastic | drift | 0.100853733 | 0.020833333 | 0.009114583 | {'complete': True, 'ate_good': False, 'survived_first': False} |

L1通过：False。

W沿用F1：L0世界一致，L1视野和L2 ES改动不影响拥有全坐标的脚本基线，轨迹不变。

## L2

配置：`configs/002a_pilot_L2.yaml`。

| arm | world | seed | generations | collapsed_at | S | ate good ≥1 | survived first | good/bad mean | seconds |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|
| gru_mb_plastic | drift | 0 | 400 | None | 0.100069010 | 0.007812500 | 0.003906250 | 0.011719/0.021484 | 339.376 |
| gru_fixed | static | 0 | 400 | None | 0.757300781 | 0.964843750 | 0.000000000 | 21.582031/1.009766 | 1035.514 |
| gru_fixed | static | 1 | 400 | None | 0.100097656 | 0.001953125 | 0.000000000 | 0.001953/0.000000 | 278.287 |
| gru_fixed | static | 2 | 400 | None | 0.751404948 | 0.943359375 | 0.000000000 | 20.753906/1.033203 | 993.616 |
| gru_fixed | drift | 0 | 400 | None | 0.099903646 | 0.000000000 | 0.000000000 | 0.000000/0.003906 | 249.735 |
| gru_fixed | drift | 1 | 400 | None | 0.100000000 | 0.000000000 | 0.000000000 | 0.000000/0.000000 | 226.168 |
| gru_fixed | drift | 2 | 400 | None | 0.099903646 | 0.000000000 | 0.000000000 | 0.000000/0.003906 | 290.657 |
| gru_mb_plastic | static | 0 | 400 | None | 0.891315104 | 0.982421875 | 0.000000000 | 26.583984/1.501953 | 2196.596 |
| gru_mb_plastic | static | 1 | 400 | None | 0.613990885 | 0.865234375 | 0.000000000 | 16.699219/0.847656 | 1334.279 |
| gru_mb_plastic | static | 2 | 400 | None | 0.779908854 | 0.923828125 | 0.000000000 | 21.042969/1.132812 | 1444.108 |
| gru_mb_plastic | drift | 1 | 400 | None | 0.105119792 | 0.068359375 | 0.050781250 | 0.226562/0.261719 | 520.584 |
| gru_mb_plastic | drift | 2 | 400 | None | 0.100049479 | 0.001953125 | 0.000000000 | 0.001953/0.001953 | 406.774 |

| arm | world | seed-average S | ate good ≥1 | survived first | absolute gate |
|---|---|---:|---:|---:|---|
| gru_fixed | static | 0.536267795 | 0.636718750 | 0.000000000 | {'complete': True, 'ate_good': False, 'survival': True} |
| gru_fixed | drift | 0.099935764 | 0.000000000 | 0.000000000 | {'complete': True, 'ate_good': False, 'survived_first': False} |
| gru_mb_plastic | static | 0.761738281 | 0.923828125 | 0.000000000 | {'complete': True, 'ate_good': True, 'survival': True} |
| gru_mb_plastic | drift | 0.101746094 | 0.026041667 | 0.018229167 | {'complete': True, 'ate_good': False, 'survived_first': False} |

L2通过：False。

W沿用F1：L0世界一致，L1视野和L2 ES改动不影响拥有全坐标的脚本基线，轨迹不变。

## L3

配置：`configs/002a_pilot_L3.yaml`。

| arm | world | seed | generations | collapsed_at | S | ate good ≥1 | survived first | good/bad mean | seconds |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|
| gru_mb_plastic | drift | 0 | 400 | None | 0.166937500 | 0.009765625 | 0.250000000 | 0.013672/0.025391 | 426.327 |
| gru_fixed | static | 0 | 400 | None | 0.803468750 | 0.962890625 | 0.000000000 | 22.728516/1.109375 | 610.920 |
| gru_fixed | static | 1 | 400 | None | 0.166968750 | 0.007812500 | 0.000000000 | 0.011719/0.013672 | 192.575 |
| gru_fixed | static | 2 | 400 | None | 0.169488281 | 0.005859375 | 0.000000000 | 0.125000/0.025391 | 266.696 |
| gru_fixed | drift | 0 | 400 | None | 0.166695312 | 0.007812500 | 0.244140625 | 0.007812/0.023438 | 138.705 |
| gru_fixed | drift | 1 | 400 | None | 0.167121094 | 0.011718750 | 0.242187500 | 0.021484/0.033203 | 139.887 |
| gru_fixed | drift | 2 | 400 | None | 0.167199219 | 0.013671875 | 0.187500000 | 0.021484/0.025391 | 171.063 |
| gru_mb_plastic | static | 0 | 400 | None | 0.909300781 | 0.996093750 | 0.000000000 | 26.294922/1.119141 | 1146.882 |
| gru_mb_plastic | static | 1 | 400 | None | 0.810954427 | 0.964843750 | 0.000000000 | 21.574219/1.146484 | 1249.665 |
| gru_mb_plastic | static | 2 | 400 | None | 0.282763021 | 0.437500000 | 0.000000000 | 3.558594/0.408203 | 750.666 |
| gru_mb_plastic | drift | 1 | 400 | None | 0.166877604 | 0.013671875 | 0.238281250 | 0.013672/0.027344 | 455.471 |
| gru_mb_plastic | drift | 2 | 400 | None | 0.166785156 | 0.013671875 | 0.185546875 | 0.015625/0.025391 | 458.415 |

| arm | world | seed-average S | ate good ≥1 | survived first | absolute gate |
|---|---|---:|---:|---:|---|
| gru_fixed | static | 0.379975260 | 0.325520833 | 0.000000000 | {'complete': True, 'ate_good': False, 'survival': False} |
| gru_fixed | drift | 0.167005208 | 0.011067708 | 0.224609375 | {'complete': True, 'ate_good': False, 'survived_first': False} |
| gru_mb_plastic | static | 0.667672743 | 0.799479167 | 0.000000000 | {'complete': True, 'ate_good': False, 'survival': True} |
| gru_mb_plastic | drift | 0.166866753 | 0.012369792 | 0.224609375 | {'complete': True, 'ate_good': False, 'survived_first': False} |

L3通过：False。

W重测通过：True；各条件：[('drift', 'H', 1.0), ('drift', 'N', 0.31878580729166667), ('drift', 'F', 0.15108919270833332), ('static', 'H', 1.0)]

逐20代及运行首尾采样温度70–92°C，图形时钟1177–2670MHz；非连续峰值。

## 失败、预算与偏离

截至该报告，没有运行NaN、崩溃或失败重跑。

逐代原始日志、检查点与逐回合指标保留在 `runs/002A/F2/`；提交的 `pilot_summaries/` 只含固定每20代摘要及最后指标。完整阶段索引 `f2_learnability.json`。

只按上述绝对指标选择阶梯，没有查看B−A差值，没有增加阶梯之外的训练手段。正式矩阵、V、保留集、消融和H1–H3均未验证。
