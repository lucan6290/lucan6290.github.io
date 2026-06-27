---
title: "Jetson Orin NANO 板载硬件信息"
date: 2025-10-10 10:00:00
categories:
  - [技术研习, Jetson_Orin_NANO]
tags: [jetson, orin-nano, 嵌入式, NVIDIA, 开发板, 硬件, tegra]
series: "Jetson Orin NANO 开发板使用笔记"
series_order: 2
description: 使用 jetson_release、nvpmodel 等命令详细查看 Jetson Orin NANO 板载硬件信息与系统配置。
cover: /img/covers/tech-study.svg
slug: ts-jetson-board-hardware
status: published
lang: zh-CN
---

## 前言

本文记录了使用 `jetson_release`、`nvpmodel`、`tegrastats` 等命令查看 Jetson Orin NANO 开发板详细硬件信息的过程。

## 一、jetson_release 输出

```bash
$ sudo jetson_release
```

```
Software part of jetson-stats 4.3.1 - (c) 2024, Raffaello Bonghi
Jetpack missing!
 - Model: NVIDIA Jetson Orin Nano Engineering Reference Developer Kit Super
 - L4T: 36.4.7
NV Power Mode[2]: MAXN_SUPER
Hardware:
 - P-Number: p3767-0005
 - Module: NVIDIA Jetson Orin Nano (Developer kit)
Platform:
 - Distribution: Ubuntu 22.04 Jammy Jellyfish
 - Release: 5.15.148-tegra
Libraries:
 - CUDA: 12.6.85
 - cuDNN: 9.16.0.29
 - TensorRT: 10.7.0.23
 - VPI: 3.2.4
 - Vulkan: 1.3.204
 - OpenCV: 4.10.0 - with CUDA: YES
```

### L4T 版本详情

```bash
$ head -n 1 /etc/nv_tegra_release
# R36 (release), REVISION: 4.7, GCID: 42132812, BOARD: generic, EABI: aarch64, DATE: Thu Sep 18 22:54:44 UTC 2025
```

## 二、nvpmodel 电源模式详情

```bash
$ sudo /usr/sbin/nvpmodel -q --verbose
```

当前模式：**NV Power Mode: MAXN_SUPER**

### CPU 核心配置

| 核心 | 在线状态 | 最小频率 | 最大频率 |
|------|---------|---------|---------|
| CORE_0 ~ CORE_5 | 全部在线 | 729600 Hz | 最大值 |

### GPU 配置

```
PARAM GPU: MIN_FREQ: 0  MAX_FREQ: 最大值
PARAM EMC: MAX_FREQ: 3199000000
```

## 三、tegrastats 实时监控

```bash
$ tegrastats
```

输出示例：

```
RAM 2161/7620MB (lfb 149x4MB) SWAP 1875/12002MB (cached 43MB)
CPU [2%@1728,1%@1728,4%@1728,2%@1728,9%@1728,1%@1728]
GR3D_FREQ 0%
cpu@55.093C soc2@53.75C soc0@54.562C gpu@56.562C tj@56.562C
VDD_IN 7256mW/7256mW VDD_CPU_GPU_CV 1711mW/1711mW VDD_SOC 2511mW/2511mW
```

### 关键参数说明

| 参数 | 含义 |
|------|------|
| RAM 2161/7620MB | 内存使用 2.1GB / 总共 7.4GB |
| SWAP 1875/12002MB | 交换分区使用 1.8GB / 总共 11.7GB |
| GR3D_FREQ 0% | GPU 当前频率利用率 |
| cpu@55.093C | CPU 温度 |
| VDD_IN 7256mW | 输入功率 |

## 四、jetson_clocks 时钟状态

```bash
$ sudo jetson_clocks --show
```

```
SOC family:tegra234  Machine:NVIDIA Jetson Orin Nano Engineering Reference Developer Kit Super
Online CPUs: 0-5
cpu0: Online=1 Governor=schedutil MinFreq=1728000 MaxFreq=1728000 CurrentFreq=1728000
cpu1: Online=1 Governor=schedutil MinFreq=1728000 MaxFreq=1728000 CurrentFreq=1728000
...
GPU MinFreq=1020000000 MaxFreq=1020000000 CurrentFreq=1020000000
Active GPU TPCs: 8
EMC MinFreq=204000000 MaxFreq=3199000000 CurrentFreq=3199000000 FreqOverride=1
FAN Dynamic Speed Control=kernel hwmon0_pwm1=88
NV Power Mode: MAXN_SUPER
```

## 五、jtop 详细面板信息

通过 `jtop` 工具可以看到更详细的硬件信息：

### 系统面板

| 项目 | 信息 |
|------|------|
| Machine | aarch64 |
| System | Linux |
| Distribution | Ubuntu 22.04 Jammy Jellyfish |
| Release | 5.15.148-tegra |
| Python | 3.10.12 |

### 硬件面板

| 项目 | 信息 |
|------|------|
| Model | NVIDIA Jetson Orin Nano Engineering Reference Developer Kit Super |
| P-Number | p3767-0005 |
| Module | NVIDIA Jetson Orin Nano (Developer kit) |
| SoC | tegra234 |
| CUDA Arch BIN | 8.7 |
| L4T | 36.4.7 |

### 库版本面板

| 组件 | 版本 |
|------|------|
| CUDA | 12.6.85 |
| cuDNN | 9.16.0.29 |
| TensorRT | 10.7.0.23 |
| VPI | 3.2.4 |
| OpenCV | 4.12.0 |

### 网络接口

| 接口 | IP 地址 |
|------|---------|
| wlP1p1s0 | 192.168.31.155 |
| docker0 | 172.17.0.1 |
