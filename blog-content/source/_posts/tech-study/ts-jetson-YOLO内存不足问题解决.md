---
title: "YOLO 运行时 Jetson 内存不足问题解决"
date: 2025-01-05 10:00:00
categories:
  - [技术研习, Jetson_Orin_NANO]
tags: [jetson, orin-nano, yolo, 内存优化, CUDA, PyTorch, 排错]
series: "Jetson Orin NANO 开发板使用笔记"
series_order: 15
description: 完整解决 Jetson 设备运行 YOLOv11 时的 PyTorch CUDA 内存分配错误，涵盖环境变量配置、Swap 优化与模型调优。
cover: /img/covers/tech-study.svg
slug: ts-jetson-yolo-memory-issue
status: published
lang: zh-CN
---

## 前言

在 Jetson 嵌入式设备上运行 YOLOv11 时，可能会遇到 PyTorch CUDA 内存分配错误导致程序崩溃。本文提供完整的解决方案。

---

## 一、问题概述

### 典型错误信息

- `NVML_SUCCESS == r INTERNAL ASSERT FAILED at ... CUDACachingAllocator.cpp`
- `NvMapMemAllocInternalTagged: ... error 12`
- `Unrecognized CachingAllocator option: heuristic`

### 问题根源

| 原因 | 说明 |
|------|------|
| **统一内存架构** | Jetson 的 GPU 与 CPU 共享同一块物理内存（8GB），深度学习任务和系统进程竞争同一资源 |
| **内存碎片化** | PyTorch 默认的内存分配器反复分配/释放后产生大量小碎片，即使总空闲内存足够也找不到连续内存块 |
| **软件版本差异** | 不同版本的 PyTorch（尤其是 Jetson 定制的 `nv` 版本）对某些内存优化参数的支持不同 |

---

## 二、解决方案

### 方案 A：设置 PyTorch 内存分配环境变量（最直接有效）

```bash
# 方案A（通用推荐）：限制内存块最小分割大小
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

# 方案B（如果方案A无效）：尝试更小的块
# export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:64
```

**永久生效**（推荐）：

```bash
echo 'export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128' >> ~/.bashrc
source ~/.bashrc
```

> **重要**：早期方案中曾建议使用 `heuristic` 参数，但此参数在某些 Jetson 定制的 PyTorch 版本中不被识别。请**优先使用 `max_split_size_mb`**。

### 方案 B：优化 Jetson 系统交换空间（Swap）

```bash
# 1. 检查当前状态
free -h
sudo swapon --show

# 2. 创建 8GB 交换文件
sudo fallocate -l 8G /home/swapfile
sudo chmod 600 /home/swapfile
sudo mkswap /home/swapfile
sudo swapon /home/swapfile

# 3. 永久生效：添加到 /etc/fstab
# /home/swapfile none swap sw 0 0
```

### 方案 C：模型与代码层面优化

```bash
# 使用更小的模型
# yolo11n.pt 或 yolo11s.pt

# 减小输入尺寸
```

```python
results = model(source="your_image.jpg", imgsz=320)
```

```python
# 及时清理缓存
torch.cuda.empty_cache()
```

---

## 三、预防与监控

### 运行前检查

```bash
# 查看内存使用概况
free -h

# 实时监控（最全面）
sudo tegrastats
```

### 关键指标

| 指标 | 含义 |
|------|------|
| **RAM 使用量** | 总内存池，包括 GPU 显存 |
| **SWAP 使用量** | RAM 吃紧时开始使用，频繁使用会极大降低速度 |
| **GR3D_FREQ** | GPU 频率，持续高频率和高温是满载标志 |

---

## 四、总结

在 Jetson 等资源受限的边缘设备上部署 YOLO，**内存管理是核心挑战**。

**记住这个组合**：监控（tegrastats）+ 预防（环境变量）+ 调优（小模型/小尺寸）

这套方法不仅适用于 YOLOv11，也普遍适用于在 Jetson 上运行其他 PyTorch 深度学习应用。
