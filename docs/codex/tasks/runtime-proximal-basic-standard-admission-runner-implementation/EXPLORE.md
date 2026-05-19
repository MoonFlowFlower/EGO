# Runtime-Proximal Basic-Standard Admission Runner Implementation - EXPLORE

## Exploration cycle 1

- question:
  - 未来 runner 是否真的需要再接 runtime，还是只需组合已存在 artifact
- hypothesis:
  - 当前最高杠杆的最小实现是 artifact-composition runner；再去碰 runtime 只会扩大风险
- observation:
  - 五层 evidence 都已经存在且结构稳定
  - 当前缺的只是 aggregate verdict，而不是新的底层采样
- decision:
  - runner 只做 artifact composition
