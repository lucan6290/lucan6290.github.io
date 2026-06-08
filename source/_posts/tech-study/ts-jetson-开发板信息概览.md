---
title: Jetson Orin NANO 开发板信息概览
date: 2025-10-08 10:00:00
updated: 2026-06-07 15:50:52

categories:
  - [技术研习, 系列专题]

tags:
  - jetson
  - orin-nano
  - 嵌入式
  - NVIDIA
  - 开发板
  - 硬件
  - jtop

description: 记录 Jetson Orin NANO SUPER 开发板的完整硬件与软件环境信息，包括系统概览、NVIDIA 软件栈版本、硬件参数等。

lang: zh-CN

cover: /img/covers/tech-study.svg

slug: ts-jetson-board-info

status: published

series: Jetson Orin NANO 开发板使用笔记
series_order: 1
---

## 前言

拿到 Jetson Orin NANO SUPER 开发板后的第一步，就是了解它的硬件规格和软件环境。本文通过 `jtop`、`jetson_release`、`nvidia-smi` 等工具，完整记录开发板的各项信息。

## 一、系统概览

| 类别 | 详细信息 |
|------|----------|
| **硬件型号** | NVIDIA Jetson Orin Nano Engineering Reference Developer Kit Super |
| **SoC 芯片** | tegra234 |
| **架构** | aarch64 (ARM64) |
| **操作系统** | Ubuntu 22.04 Jammy Jellyfish |
| **内核版本** | 5.15.148-tegra |
| **主机名** | yahboom |
| **Python 版本** | 3.10.12 |

### 硬件标识

- **P-Number**: p3767-0005
- **模块型号**: NVIDIA Jetson Orin Nano (Developer kit)
- **699 级部件号**: 699-13767-0005-300 T.1
- **CUDA 计算能力**: 8.7

## 二、NVIDIA 软件栈版本

| 组件 | 版本号 | 备注 |
|------|--------|------|
| **JetPack SDK** | 6.2 | 完整的 NVIDIA 开发套件 |
| **L4T (Linux for Tegra)** | 36.4.3 | Jetson 专用 Linux 系统 |
| **CUDA** | 12.6.85 | 并行计算平台 |
| **cuDNN** | 9.16.0.29 | 深度神经网络库 |
| **TensorRT** | 10.7.0.23 | 高性能推理优化器 |
| **VPI** | 3.2.4 | 视觉编程接口 |
| **Vulkan** | 1.3.204 | 图形和计算 API |
| **OpenCV** | 4.10.0 | 带 CUDA 加速支持 |

## 三、CPU 信息

通过 `lscpu` 查看 CPU 详情：

```
Architecture:            aarch64
CPU(s):                  6
Vendor ID:               ARM
Model name:            Cortex-A78AE
Thread(s) per core:  1
Core(s) per cluster: 3
Cluster(s):          2
CPU max MHz:         1728.0000
CPU min MHz:         115.2000
```

### 缓存信息

| 缓存级别 | 大小 |
|----------|------|
| L1d | 384 KiB (6 instances) |
| L1i | 384 KiB (6 instances) |
| L2 | 1.5 MiB (6 instances) |
| L3 | 4 MiB (2 instances) |

## 四、内存与存储

```bash
$ free -h
               total        used        free      shared  buff/cache   available
Mem:           7.4Gi       2.0Gi       5.0Gi        29Mi       387Mi       5.2Gi
Swap:           11Gi       1.8Gi       9.9Gi
```

## 五、GPU 信息

通过 `nvidia-smi` 查看：

```
+---------------------------------------------------------------------------------------+
| NVIDIA-SMI 540.4.0                Driver Version: 540.4.0      CUDA Version: 12.6     |
|-----------------------------------------+----------------------+----------------------+
|   0  Orin (nvgpu)                  N/A  | N/A              N/A |                  N/A |
+-----------------------------------------+----------------------+----------------------+
```

## 六、网络配置

- **无线网络 (wlP1p1s0)**: 192.168.31.155
- **Docker 网络 (docker0)**: 172.17.0.1
- **ROS Domain ID**: 99
- **ROS 版本**: Humble

## 七、Python 环境管理（Conda/Miniforge）

- **Conda 版本**: 25.9.1
- **环境管理器**: libmamba（高性能求解器）
- **环境位置**: `/home/jetson/miniforge3`
- **平台**: `linux-aarch64`

### 当前 Conda 环境

```
# conda environments:
#
base                     /home/jetson/miniforge3
python310_llm            /home/jetson/miniforge3/envs/python310_llm
python310_yolo       *   /home/jetson/miniforge3/envs/python310_yolo
```

## 八、性能状态（jtop 截图）

通过 `jtop` 实时监控可以看到：

- **电源模式**: MAXN_SUPER（高性能模式）
- **CPU 频率**: 全部 1.7GHz
- **GPU 频率**: 1.0GHz
- **温度**: CPU 约 54°C，GPU 约 55°C
- **功耗**: VDD_IN 约 7.3W

## 九、环境状态总结

### ✅ 已完整配置的组件

- **完整的 NVIDIA AI 堆栈**: JetPack 6.2 + 所有核心组件
- **开发环境**: Python 3.10 + OpenCV with CUDA
- **机器人开发**: ROS2 Humble 环境
- **容器支持**: Docker 网络已配置

### ⚡ 性能特性

- **CUDA 计算能力**: 8.7（支持最新 CUDA 特性）
- **电源模式**: MAXN_SUPER（高性能模式）
- **完整的 GPU 加速**: 支持 CUDA、TensorRT、Vulkan 等
