# EVOLAB-002A 试跑次要指标

只描述已有pilot开发回合，不是保留集或消融分析。每个种子独立统计；从未经历切换记为no_switches，中位数未降到50%记为not_reached。死亡、时限或下一次切换使未恢复事件右截尾。同一步切换并吃到好食物记0步；同一时刻的恢复先于截尾移出风险集。

采用 [NIST所述的Kaplan–Meier乘积极限估计](https://itl.nist.gov/div898/handbook/apr/section2/apr215.htm)。死亡/下一次切换可能构成信息性截尾，因此只作描述，不推断死亡后的反事实恢复，不参与任何闸门或H1–H3判定。

| level | arm | world | seed | good mean | bad mean | switches | censored | censor fraction | KM median steps | status | collapsed_at |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| L0 | gru_mb_plastic | drift | 0 | 0.269531 | 0.347656 | 22 | 21 | 0.954545 | N/A | not_reached | None |
| L0 | gru_fixed | static | 0 | 0.076172 | 0.005859 | 0 | 0 | N/A | N/A | no_switches | 341 |
| L0 | gru_fixed | static | 1 | 2.427734 | 0.619141 | 0 | 0 | N/A | N/A | no_switches | None |
| L0 | gru_fixed | static | 2 | 0.765625 | 0.353516 | 0 | 0 | N/A | N/A | no_switches | None |
| L0 | gru_fixed | drift | 0 | 0.148438 | 0.169922 | 14 | 13 | 0.928571 | N/A | not_reached | None |
| L0 | gru_fixed | drift | 1 | 0.011719 | 0.017578 | 2 | 2 | 1.000000 | N/A | not_reached | None |
| L0 | gru_fixed | drift | 2 | 0.058594 | 0.060547 | 5 | 5 | 1.000000 | N/A | not_reached | None |
| L0 | gru_mb_plastic | static | 0 | 0.615234 | 0.298828 | 0 | 0 | N/A | N/A | no_switches | None |
| L0 | gru_mb_plastic | static | 1 | 0.160156 | 0.072266 | 0 | 0 | N/A | N/A | no_switches | None |
| L0 | gru_mb_plastic | static | 2 | 2.107422 | 0.443359 | 0 | 0 | N/A | N/A | no_switches | None |
| L0 | gru_mb_plastic | drift | 1 | 0.005859 | 0.009766 | 0 | 0 | N/A | N/A | no_switches | None |
| L0 | gru_mb_plastic | drift | 2 | 0.093750 | 0.050781 | 7 | 7 | 1.000000 | N/A | not_reached | None |
| L1 | gru_mb_plastic | drift | 0 | 0.003906 | 0.003906 | 0 | 0 | N/A | N/A | no_switches | 330 |
| L1 | gru_fixed | static | 0 | 1.265625 | 0.462891 | 0 | 0 | N/A | N/A | no_switches | None |
| L1 | gru_fixed | static | 1 | 0.683594 | 0.363281 | 0 | 0 | N/A | N/A | no_switches | None |
| L1 | gru_fixed | static | 2 | 0.369141 | 0.189453 | 0 | 0 | N/A | N/A | no_switches | None |
| L1 | gru_fixed | drift | 0 | 0.119141 | 0.250000 | 11 | 10 | 0.909091 | N/A | not_reached | None |
| L1 | gru_fixed | drift | 1 | 0.125000 | 0.181641 | 11 | 9 | 0.818182 | 181 | reached | None |
| L1 | gru_fixed | drift | 2 | 0.076172 | 0.066406 | 6 | 6 | 1.000000 | N/A | not_reached | None |
| L1 | gru_mb_plastic | static | 0 | 1.623047 | 0.359375 | 0 | 0 | N/A | N/A | no_switches | None |
| L1 | gru_mb_plastic | static | 1 | 1.431641 | 0.296875 | 0 | 0 | N/A | N/A | no_switches | None |
| L1 | gru_mb_plastic | static | 2 | 0.517578 | 0.371094 | 0 | 0 | N/A | N/A | no_switches | None |
| L1 | gru_mb_plastic | drift | 1 | 0.003906 | 0.001953 | 0 | 0 | N/A | N/A | no_switches | 373 |
| L1 | gru_mb_plastic | drift | 2 | 0.136719 | 0.191406 | 14 | 13 | 0.928571 | N/A | not_reached | None |
| L2 | gru_mb_plastic | drift | 0 | 0.011719 | 0.021484 | 2 | 2 | 1.000000 | N/A | not_reached | None |
| L2 | gru_fixed | static | 0 | 21.582031 | 1.009766 | 0 | 0 | N/A | N/A | no_switches | None |
| L2 | gru_fixed | static | 1 | 0.001953 | 0.000000 | 0 | 0 | N/A | N/A | no_switches | None |
| L2 | gru_fixed | static | 2 | 20.753906 | 1.033203 | 0 | 0 | N/A | N/A | no_switches | None |
| L2 | gru_fixed | drift | 0 | 0.000000 | 0.003906 | 0 | 0 | N/A | N/A | no_switches | None |
| L2 | gru_fixed | drift | 1 | 0.000000 | 0.000000 | 0 | 0 | N/A | N/A | no_switches | None |
| L2 | gru_fixed | drift | 2 | 0.000000 | 0.003906 | 0 | 0 | N/A | N/A | no_switches | None |
| L2 | gru_mb_plastic | static | 0 | 26.583984 | 1.501953 | 0 | 0 | N/A | N/A | no_switches | None |
| L2 | gru_mb_plastic | static | 1 | 16.699219 | 0.847656 | 0 | 0 | N/A | N/A | no_switches | None |
| L2 | gru_mb_plastic | static | 2 | 21.042969 | 1.132812 | 0 | 0 | N/A | N/A | no_switches | None |
| L2 | gru_mb_plastic | drift | 1 | 0.226562 | 0.261719 | 27 | 26 | 0.962963 | N/A | not_reached | None |
| L2 | gru_mb_plastic | drift | 2 | 0.001953 | 0.001953 | 0 | 0 | N/A | N/A | no_switches | None |
| L3 | gru_mb_plastic | drift | 0 | 0.013672 | 0.025391 | 135 | 134 | 0.992593 | N/A | not_reached | None |
| L3 | gru_fixed | static | 0 | 22.728516 | 1.109375 | 0 | 0 | N/A | N/A | no_switches | None |
| L3 | gru_fixed | static | 1 | 0.011719 | 0.013672 | 0 | 0 | N/A | N/A | no_switches | None |
| L3 | gru_fixed | static | 2 | 0.125000 | 0.025391 | 0 | 0 | N/A | N/A | no_switches | None |
| L3 | gru_fixed | drift | 0 | 0.007812 | 0.023438 | 132 | 132 | 1.000000 | N/A | not_reached | None |
| L3 | gru_fixed | drift | 1 | 0.021484 | 0.033203 | 125 | 125 | 1.000000 | N/A | not_reached | None |
| L3 | gru_fixed | drift | 2 | 0.021484 | 0.025391 | 99 | 99 | 1.000000 | N/A | not_reached | None |
| L3 | gru_mb_plastic | static | 0 | 26.294922 | 1.119141 | 0 | 0 | N/A | N/A | no_switches | None |
| L3 | gru_mb_plastic | static | 1 | 21.574219 | 1.146484 | 0 | 0 | N/A | N/A | no_switches | None |
| L3 | gru_mb_plastic | static | 2 | 3.558594 | 0.408203 | 0 | 0 | N/A | N/A | no_switches | None |
| L3 | gru_mb_plastic | drift | 1 | 0.013672 | 0.027344 | 123 | 123 | 1.000000 | N/A | not_reached | None |
| L3 | gru_mb_plastic | drift | 2 | 0.015625 | 0.025391 | 98 | 98 | 1.000000 | N/A | not_reached | None |
