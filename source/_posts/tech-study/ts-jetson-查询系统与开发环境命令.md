---
title: "查询系统与开发环境信息的实用命令"
date: 2025-01-10 10:00:00
categories:
  - [技术研习, 系列专题]
tags: [jetson, orin-nano, 命令参考, 系统查询, CUDA, PyTorch, ROS]
series: "Jetson Orin NANO 开发板使用笔记"
series_order: 16
description: 在 Jetson Orin NANO 上查询系统信息、NVIDIA 软件栈版本、Python 环境、Ollama 服务和 ROS 2 环境的实用命令汇总。
cover: /img/covers/tech-study.svg
slug: ts-jetson-query-commands
status: published
lang: zh-CN
---

## 前言

在 Jetson 开发板上，快速了解系统状态和环境信息是日常开发的基础。本文整理了查询系统、开发环境及深度学习环境版本信息的实用命令。

---

## 一、速查命令表

| 查询目标 | 关键命令 | 备注 |
|---------|---------|------|
| **系统与 JetPack 信息** | `sudo jetson_release` | 查看 JetPack、L4T 等核心组件版本 |
| **CUDA 版本** | `nvcc --version` 或 `nvidia-smi` | 检查 CUDA 编译器版本 |
| **cuDNN 版本** | `cat /usr/include/cudnn_version.h \| grep CUDNN_MAJOR -A 2` | 可能需要调整路径 |
| **TensorRT 版本** | `dpkg -l \| grep tensorrt` | 通过包管理器查询 |
| **Python 环境** | `python3 --version` 或 `pip3 list` | 查看版本和已安装包 |
| **Conda 环境** | `conda --version` 及 `conda info` | 确认安装及环境信息 |
| **PyTorch 环境** | `import torch; print(torch.__version__)` | 验证 PyTorch 及 CUDA 支持 |
| **Ollama 服务** | `ollama --version` 及 `systemctl status ollama` | 版本与服务状态 |
| **ROS 2 环境** | `echo $ROS_DISTRO` 及 `ros2 version` | 查看发行版和版本 |

---

## 二、系统与 NVIDIA 核心环境

`jtop` 工具能**实时监控**硬件状态和库版本，是管理 Jetson 设备的利器：

```bash
sudo jtop
```

---

## 三、Python 与 Conda 环境管理

Jetson 是 ARM64 架构，不能直接安装 x86 版本的 Anaconda。推荐安装 **Miniforge**：

```bash
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh
bash Miniforge3-Linux-aarch64.sh
source ~/.bashrc
```

### 创建并激活虚拟环境

```bash
conda create -n my_project python=3.10
conda activate my_project
```

### 验证 PyTorch

```python
import torch
print(f"PyTorch版本: {torch.__version__}")
print(f"CUDA是否可用: {torch.cuda.is_available()}")
print(f"CUDA版本: {torch.version.cuda}")
```

---

## 四、Ollama 大模型部署

```bash
# 安装
curl -fsSL https://ollama.com/install.sh | sh

# 运行模型
ollama run llama3.2:3b
```

---

## 五、ROS 2 开发环境

```bash
# 验证 ROS 2 环境
source /opt/ros/humble/setup.bash
ros2 topic list
```

---

## 六、高效管理建议

1. **善用虚拟环境**：使用 Conda 为不同项目创建独立环境，避免依赖冲突
2. **关注存储空间**：大型模型占用大量空间，可将模型存储路径设置到外接 SSD
3. **组合使用命令**：将查询命令写成脚本，方便快速生成系统状态报告
