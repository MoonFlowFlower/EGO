# EVOLAB-001A — E0 环境检查（阻断）

检查日期：2026-10-02，America/Winnipeg（UTC−05:00）。状态：**BLOCKED / E0 未通过**。

## 检查范围与停止决定

已按顺序读取 STAGE_CARD、PREREG_E2、DESIGN、ENVIRONMENT、RESEARCH_BACKGROUND、JAXLIFE_ASSESSMENT。按 STAGE_CARD 第 3、6 节及用户停止要求，WSL2 无法启动时停止实验，不进入 E1/E2。此次属于环境工程阻断，没有科学结果，不能判为科学负结果。

文档基点：`14dc7cb86b5407523d33692fe190a3d837ef639b`，分支 `codex/desktop-pet-memory-lab-20261001`。远端指定分支已有 evolab 文档，无需切换备用分支。

当前 Windows 工作目录不是 Git 仓库，实际使用其已有 `.publish/EGO` checkout 保存本报告；已从 `869a030` 快进同步文档。同步包含远端已有 TASK_BOARD 变更，本次不编辑或提交任何 evolab 以外文件。WSL 启动前置检查在读取研究文档前已执行；此顺序偏离已记录，未因此执行实现或训练。

## 实测版本与设备

| 项目 | 观测 |
|---|---|
| Windows（`wsl --version`） | 10.0.26100.6584 |
| WSL 包版本 | 2.6.3.0 |
| WSL 报告的 kernel 版本 | 6.6.87.2-1（不代表本次已启动） |
| 发行版登记 | Ubuntu / Stopped / VERSION 2；Ubuntu 具体发行版版本未验证 |
| GPU（Windows `nvidia-smi`） | NVIDIA GeForce RTX 5070 Ti Laptop GPU |
| 总显存 | **12227 MiB**，不同于任务描述的 16GB |
| Windows NVIDIA 驱动 | 616.56 |
| NVIDIA-SMI 报告 CUDA UMD Version | 13.4；不等同于已安装 Linux CUDA toolkit 或 JAX 运行库版本 |
| 固件虚拟化 | `VirtualizationFirmwareEnabled=True` |
| VMMonitorModeExtensions / SLAT | True / True |
| Windows hypervisor | `HypervisorPresent=False` |
| Windows 服务 | WslService=Running/Automatic；vmcompute、hns 查询均返回找不到服务 |
| Linux NVIDIA 驱动可见性 / CUDA 运行库 | 未验证：无法启动 WSL |
| Python / JAX / jaxlib / CUDA plugin 版本 | 未验证：未进入 Linux，也未安装或降级依赖 |
| sm_120 内核兼容性 | 未验证 |

## 失败命令与输出

`wsl --list --verbose` 成功返回登记的 Ubuntu，版本 2，状态 Stopped。

唯一一次启动尝试（退出码 1）：

```powershell
wsl -d Ubuntu -- bash -lc 'pwd; id; ls -la ~; command -v git; command -v gh'
```

```text
The operation could not be started because a required feature is not installed.
Error code: Wsl/Service/CreateInstance/CreateVm/HCS/HCS_E_SERVICE_NOT_AVAILABLE
```

只读诊断命令：

```powershell
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
```

```text
NVIDIA GeForce RTX 5070 Ti Laptop GPU, 12227 MiB, 616.56
```

`Get-CimInstance Win32_ComputerSystem` 和 `Win32_Processor` 的相关字段见上表。以下查询没有获取到功能状态：

```powershell
Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
```

两条均报 `The requested operation requires elevation.`，故不能声称这两个功能已确认关闭。另一次 `bcdedit /enum '{current}'` 查询报 `The specified entry type is invalid.` / `The parameter is incorrect.`，启动配置未验证；不据此推断 hypervisorlaunchtype。

工作区初次执行 Git 查询报 `not a git repository`，随后定位到已有 `.publish/EGO`。根 AGENTS 指定的三个上下文文件直接文件读取失败（当前 checkout 中不存在），后续使用 `git show HEAD:<path>` 成功读取对应 Git 对象。这些是诊断失败，不是实验运行失败。

诊断推断：阻断位于 Windows 的 WSL2 虚拟机启动层，尚未触及 JAX。功能是否未启用、启动设置是否关闭 hypervisor 等具体原因**未验证**。此次没有修补尝试，没有修改 Windows 功能、驱动、启动配置，也没有重启机器。

## E0 要求的性能与确定性证据

| 必测项 | 结果 |
|---|---|
| WSL 内 `nvidia-smi` | 未验证 |
| `jax.__version__` / `jax.devices()` | 未验证；没有输出，不能填入 Windows GPU 查询作为替代 |
| 4096×4096 float32 矩阵乘 GFLOP/s | 未验证 |
| 确定性开关与两次计算比较 | 未验证 |
| Room-v0 随机动作 2048 / 4096 / 8192 回合吞吐 | 未验证；世界尚未实现 |
| 跨新进程适应度曲线重放 | 未验证 |
| E1 存活率、GIF、测试 | 未验证；E1 未开始 |
| E2 单次完整运行耗时 / 20 次预算外推 | 未验证 |

E2 完成数 **0/20**；本任务训练消耗 **0 GPU 小时**（没有训练进程启动，不是 GPU 计量采样）。没有配置冻结，没有使用开发或保留集种子，没有产生或丢弃训练运行。PREREG_E2 文件未修改，其检查时 SHA-256 为 `B0B8E3939A3CF22B1FB7071E576CAE8AA9EC71D93CC25D33635D131FCC15E082`（文档校验值，不是 E2 配置冻结值）。

## 恢复路径（尚未执行）

1. 用户在管理员 PowerShell 中核查 VirtualMachinePlatform、Microsoft-Windows-Subsystem-Linux 与 hypervisor 启动配置，再处理缺失功能；系统修改及重启等待用户安排。微软官方说明 WSL2 需要 Virtual Machine Platform，并列出启用命令及重启要求：[安装步骤](https://learn.microsoft.com/en-us/windows/wsl/install-manual#step-3---enable-virtual-machine-feature)、[故障排查](https://learn.microsoft.com/en-us/windows/wsl/troubleshooting)。这些指导不能证明当前机器的具体根因。
2. Ubuntu 能启动后，确认发行版版本及 WSL 内 GPU 可见性，再将指定分支克隆到 Linux 原生文件系统（如 `~/EGO`）。目前未建立或验证该克隆；不能把本 Windows 证据 checkout 当作实验运行目录。
3. 在 Linux venv 安装并锁定实测依赖，补齐 E0；通过后才进入 E1。按实际 Laptop GPU 性能重新测量预算，不沿用 16GB 桌面卡估算。

本报告仅证明环境启动阻断及上述 Windows 观测，不证明 GPU/JAX 可用性、世界有效性或任何研究结论。
