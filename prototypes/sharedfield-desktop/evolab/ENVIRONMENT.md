# EVOLAB 运行环境（RTX 5070 Ti Laptop / Windows 原生）

修订：2026-10-02。E0 第一次尝试时 WSL2 无法启动，原因是 Windows 没有运行 hypervisor，详见 `evidence/E0_ENV.md`。因此主路径改为 **Windows 原生 + PyTorch**，WSL2 + JAX 保留为备选。框架变化不影响 `PREREG_E2.md`，预注册的假设、指标和阈值与框架无关。

## 实机（E0 实测）

- GPU：NVIDIA GeForce RTX 5070 Ti **Laptop**，显存 12227 MiB（不是 16GB）
- 驱动：616.56，CUDA UMD 13.4
- 系统：Windows 10.0.26100

Room-v0 规模很小，12GB 显存预计足够。笔记本 GPU 长时间满载会降频，正式运行时要插电源，并打开高性能电源模式；GPU 时钟和温度变化记录在 `E0_ENV.md` 或运行日志里。

## 主路径：Windows 原生 + PyTorch（CUDA 12.8 及以上）

已查明的事实：
- PyTorch 2.7 及以后的稳定版，凡是基于 CUDA 12.8 及以上构建的轮子（cu128 等），都带 Blackwell sm_120 内核。
- Windows 上可以直接 pip 安装，不需要 WSL，也不需要单独安装 CUDA Toolkit，运行库已经打包在轮子里。

步骤（E0 执行并把实际输出记下来）：

1. 建 Python 3.11 或 3.12 的虚拟环境，放在 `evolab/.venv`（已被 gitignore）。
2. 用 PyTorch 官网当前推荐的 cu128 或更新的索引安装，例如 `pip install torch --index-url https://download.pytorch.org/whl/cu128`。具体命令以 https://pytorch.org/get-started/locally/ 为准。然后锁定实际安装的版本，写入 `requirements-evolab.txt`。
3. 冒烟测试，每项记录输出：
   - 打印 `torch.__version__`、`torch.version.cuda`、`torch.cuda.is_available()`、`torch.cuda.get_device_name(0)`、`torch.cuda.get_device_capability(0)`，最后一项应为 (12, 0)；
   - 跑 4096×4096 float32 矩阵乘，记录 GFLOP/s；同时用 TF32 关和开各测一次，正式运行一律关掉 TF32；
   - 确定性检查：设置环境变量 `CUBLAS_WORKSPACE_CONFIG=:4096:8`，调用 `torch.use_deterministic_algorithms(True)`，同一计算跑两次，结果必须逐位一致。
4. 出现 `no kernel image is available`、`sm_120 is not compatible` 之类错误时，先确认装的是 cu128 及以上的轮子，不是 cpu 版或 cu126 版。不要靠猜测降级。仍然失败就停下报告。

## 实现约定（替代 DESIGN 中 JAX 专有的部分）

- **批量**：所有回合放在一个批张量里。形状为 [种群 × 每候选回合数]，例如 256×8=2048，再加状态维度。每一步对整个批做一次张量运算。不要按个体或回合写 Python 循环。
- **时间循环**：回合内的 1500 步可以用 Python 循环。每步的 kernel 启动开销要实测；太慢时再考虑 `torch.compile` 或 CUDA Graphs，并在 `PROGRESS.md` 记录用了哪个。
- **随机性**：每一代、每个用途分别用独立的 `torch.Generator`（放在 CUDA 设备上），种子由配置派生，例如 `hash(配置种子, 代号, 用途)`。不要依赖全局 RNG 状态。
- **参数**：每个候选的网络参数存成形状为 [种群, 参数维数] 的展平张量，前向时用批量矩阵乘（`torch.bmm` 或 `einsum`），相当于对种群做 vmap。
- **ES 的 Adam**：自己实现，或用 `torch.optim.Adam` 作用在均值向量上，二选一并记录。

## 备选：WSL2 + JAX

只有用户决定修复 WSL 时才走这条路。E0 观测到 `HypervisorPresent=False`，并且找不到 vmcompute 服务，这与"虚拟机平台功能未启用或 hypervisor 没有启动"相符，但具体根因未验证。修复需要管理员权限和重启，由用户自己执行，实施代理不得擅自改系统配置：

- 管理员 PowerShell：`dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart`
- 如有必要：`bcdedit /set hypervisorlaunchtype auto`
- 重启后再执行 `wsl -d Ubuntu`

注意：开启 hypervisor 可能影响部分游戏反作弊程序和其他虚拟化软件。恢复后按本文件上一版的 JAX 步骤操作，参见 git 历史，提交 `92c439c`。

## 参考

- PyTorch 安装：https://pytorch.org/get-started/locally/
- PyTorch 论坛关于 sm_120 的讨论（cu128 构建支持 Blackwell）：https://discuss.pytorch.org/t/pytorch-support-for-sm120/216099
- JAX 安装文档（CUDA 版只有 Linux 轮子）：https://docs.jax.dev/en/latest/installation.html
- WSL 手动安装与虚拟机平台：https://learn.microsoft.com/en-us/windows/wsl/install-manual
