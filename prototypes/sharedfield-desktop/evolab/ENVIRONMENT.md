# EVOLAB 运行环境（RTX 5070 Ti / Windows）

本文的事实来自 2026-10-02 的资料检索，**未在用户机器上验证**。E0 阶段要把每一项的实测结果写进 `evidence/E0_ENV.md`。

## 已知约束

- JAX 的 CUDA 版 pip 包只提供 Linux 版本。Windows 原生环境没有 JAX GPU 支持，必须在 **WSL2** 里运行。
- RTX 5070 Ti 是 Blackwell 架构，计算能力 sm_120，至少需要 CUDA 12.8（推荐 12.9 及以上）。JAX 的 `jax[cuda12]` 包会自带 CUDA 运行库，但 JAX 版本必须足够新，才包含或能即时编译 sm_120 的内核。
- 显存 16GB。Room-v0 规模很小，显存预计不是瓶颈；先按 E0 实测为准。

## 建议步骤（E0 执行并记录）

1. Windows 侧：把 NVIDIA 驱动更新到支持 CUDA 12.8 以上的版本，然后在 PowerShell 里运行 `nvidia-smi` 并记录输出。
2. 安装 WSL2，发行版选 Ubuntu 24.04。**不要**在 WSL 里面再装 Linux 版 NVIDIA 驱动，WSL 会直接使用 Windows 驱动。在 WSL 内运行 `nvidia-smi`，应能看到 GPU。
3. 代码放在 WSL 自己的文件系统里，例如 `~/EGO`。不要放在 `/mnt/d/...` 下，否则文件读写会很慢。
4. 建 Python 3.11 或 3.12 的虚拟环境，执行 `pip install -U "jax[cuda12]"`，再装 `requirements-evolab.txt` 里的其余依赖，并锁定版本。
5. 冒烟测试：
   - `python -c "import jax; print(jax.__version__, jax.devices())"` 的输出应包含 CUDA 设备；
   - 跑一个 4096×4096 的 float32 矩阵乘，记录 GFLOP/s；
   - 设置 `XLA_FLAGS=--xla_gpu_deterministic_ops=true` 后，确认同一计算两次结果一致。
6. 如果出现 `no kernel image is available` 或 sm_120 相关错误：先升级 jax 和 jaxlib，并查 JAX 官方安装文档里 Blackwell 的说明。**不要**猜测性地降级或改用 CPU 跑正式规模。仍然失败就停止，并在报告里写清楚当时的版本组合。

## 吞吐基准（E0 必测）

用 Room-v0 世界加随机动作，测量每秒个体步数，测三档：
- 种群 256 × 8 回合，同时 `vmap` 的回合数为 2048；
- 种群 512 × 8；
- 种群 1024 × 8。

用测得的数字核算 `DESIGN.md` 第 4 节的预算。

## 参考

- JAX 安装文档：https://docs.jax.dev/en/latest/installation.html
- 社区关于 RTX 5070 Ti、WSL2 与 Blackwell 的配置经验（主要讲 PyTorch，CUDA 和 sm_120 的要求相同）：https://fahimkabir2213.medium.com/setting-up-a-local-ai-workstation-on-an-rtx-5070-ti-blackwell-with-wsl2-every-step-and-every-41fb7f553673
