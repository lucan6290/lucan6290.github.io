---
title: "Miniforge 安装 —— Miniforge vs Miniconda 选择指南"
date: 2025-10-20 10:00:00
categories:
  - [技术研习, 系列专题]
tags: [jetson, orin-nano, miniforge, conda, python, 包管理, ARM64]
series: "Jetson Orin NANO 开发板使用笔记"
series_order: 4
description: 在 Jetson Orin NANO 上安装 Miniforge 的完整指南，对比 Miniforge 与 Miniconda 的区别，解释为何推荐 Miniforge。
cover: /img/covers/tech-study.svg
slug: ts-jetson-miniforge
status: published
lang: zh-CN
---

## 前言

在 Jetson Orin NANO 上管理 Python 环境，首先要选择合适的 Conda 发行版。本文对比 Miniforge 和 Miniconda 的差异，并提供 Miniforge 的完整安装指南。

---

## 一、Miniforge vs Miniconda 详细对比

### 核心区别

| 特性 | **Miniforge** | **Miniconda** |
|------|---------------|---------------|
| **默认频道** | `conda-forge` | `defaults`（Anaconda 官方） |
| **架构支持** | **原生支持 ARM64** | x86_64 为主，ARM 支持有限 |
| **包来源** | conda-forge 社区 | Anaconda 官方仓库 |
| **包更新** | 更频繁、更新快 | 较保守、稳定性优先 |
| **许可证** | BSD 许可证 | 商业使用有限制 |

### 为什么在 Jetson 上推荐 Miniforge？

**架构兼容性问题：**

- Miniconda 在 ARM 设备上：很多包没有 ARM64 预编译版本，需要从源码编译，耗时且易出错
- Miniforge 专为 ARM 优化：conda-forge 提供大量 ARM64 预编译包，依赖关系针对 ARM 架构优化

**实际体验对比：**

| 场景 | Miniforge 体验 | Miniconda 体验 |
|------|---------------|---------------|
| 安装 PyTorch | `conda install pytorch torchvision` ✅ | 可能需要从源码编译 ❌ |
| 安装 TensorFlow | `conda install tensorflow` ✅ | 依赖关系复杂 ❌ |
| 包可用性 | 丰富，预编译 ✅ | 有限，需要编译 ❌ |

### 可以安装 Miniconda 吗？

技术上可以，但不推荐：

```bash
# Miniconda ARM 版本安装（不推荐）
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh
bash Miniconda3-latest-Linux-aarch64.sh
```

---

## 二、Miniforge 详细安装指南

### 第一步：下载安装脚本

```bash
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh
```

**命令详解：**
- `Linux-aarch64.sh`：专门针对 ARM64 架构（Jetson 的架构）的安装脚本

**验证下载：**

```bash
ls -lh Miniforge3-Linux-aarch64.sh
chmod +x Miniforge3-Linux-aarch64.sh
```

### 第二步：运行安装脚本

```bash
bash Miniforge3-Linux-aarch64.sh
```

**安装过程中的关键步骤：**

1. **阅读许可证协议** — 按 `Enter` 逐页浏览，最后输入 `yes` 接受
2. **选择安装位置** — 默认 `/home/jetson/miniforge3`，推荐使用默认位置
3. **初始化 Conda** — 输入 `yes`，自动将 Conda 添加到 `~/.bashrc`

### 第三步：激活安装

```bash
source ~/.bashrc
```

**验证安装：**

```bash
conda --version
conda info
conda env list
```

### 第四步：配置 Conda 环境

```bash
# 添加 conda-forge 为主要频道
conda config --add channels conda-forge

# 设置频道优先级为严格模式
conda config --set channel_priority strict
```

**配置详解：**

- `conda config --add channels conda-forge` — conda-forge 提供最新软件包和最好的 ARM64 支持
- `conda config --set channel_priority strict` — 避免不同频道的包版本冲突

### 第五步：测试安装结果

```bash
# 创建测试环境
conda create -n test_env python=3.10
conda activate test_env

# 安装基础包测试
conda install numpy pandas matplotlib

# 验证
python -c "import numpy; print('NumPy 安装成功!')"

# 清理测试环境
conda deactivate
conda remove -n test_env --all
```

---

## 三、安装后的目录结构

```
/home/jetson/
├── miniforge3/                 # Miniforge 主目录
│   ├── bin/                    # 可执行文件（conda, python 等）
│   ├── envs/                   # 所有虚拟环境存储位置
│   ├── pkgs/                   # 包缓存目录
│   └── conda-meta/             # Conda 元数据
└── .bashrc                     # 已添加 conda 初始化脚本
```

---

## 四、重要提示

1. **安装位置**：默认安装在用户主目录下，不会影响系统 Python
2. **权限**：不需要 `sudo`，所有操作在用户权限内完成
3. **网络**：确保 Jetson 设备网络连接稳定
4. **存储空间**：Conda 环境和包会占用一定磁盘空间，注意管理

## 五、故障排除

```bash
# 如果 conda 命令找不到，手动初始化
source /home/jetson/miniforge3/bin/activate
conda init bash

# 如果安装中断，重新运行安装脚本
bash Miniforge3-Linux-aarch64.sh -u
```
