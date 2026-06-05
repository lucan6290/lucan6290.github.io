---
title: "YOLO 后台独立训练 —— nohup 与 screen"
date: 2025-12-28 10:00:00
categories:
  - [技术研习, 系列专题]
tags: [jetson, orin-nano, yolo, 训练, nohup, screen, 后台运行, SSH]
series: "Jetson Orin NANO 开发板使用笔记"
series_order: 14
description: 在 Jetson Orin NANO 上通过 SSH 远程运行 YOLO 训练任务，使用 nohup 实现断开连接后训练继续运行。
cover: /img/covers/tech-study.svg
slug: ts-jetson-yolo-background-training
status: published
lang: zh-CN
---

## 前言

通过 SSH 连接 Jetson 运行 YOLO 训练时，一旦断开连接，训练进程就会停止。本文介绍如何使用 `nohup` 让训练在后台独立运行，断开 SSH 后依然继续。

---

## 一、问题场景

> 如果直接通过 SSH 或远程桌面连接运行训练命令，退出连接会直接导致训练进程停止。

解决方案：让训练进程与当前终端会话"解绑"，使其在后台独立运行。

---

## 二、方法一：使用 nohup（最简单常用）

### 启动训练

```bash
nohup python train.py > train.log 2>&1 &
```

**参数说明**：
- `nohup python train.py`：使程序不挂断（忽略 HUP 信号）
- `> train.log`：将标准输出重定向到日志文件
- `2>&1`：将标准错误也重定向到同一文件
- `&`：让命令在后台执行

### 查看训练日志

```bash
# 实时查看日志输出
tail -f train.log
```

### 管理进程

```bash
# 查看后台进程
jobs

# 或通过 ps 查找
ps aux | grep python

# 终止进程
kill <PID>
```

---

## 三、实际使用示例

```bash
# 启动 YOLO 训练（300 epochs，日志输出到文件）
nohup python train.py > hand11_300epochs_1.log 2>&1 &

# 实时监控训练进度
tail -f hand11_300epochs_1.log
```

---

## 四、nohup 命令详解

| 组成部分 | 作用 |
|---------|------|
| `nohup` | No Hang Up，忽略挂断信号 |
| `python train.py` | 实际执行的训练命令 |
| `> train.log` | 标准输出重定向到文件 |
| `2>&1` | 标准错误合并到标准输出 |
| `&` | 放到后台执行 |

---

## 五、常见操作

```bash
# 查看所有后台 Python 进程
ps aux | grep python | grep -v grep

# 查看训练是否还在运行
ps aux | grep train.py

# 如果需要终止训练
kill $(pgrep -f train.py)

# 强制终止
kill -9 $(pgrep -f train.py)
```

---

## 六、最佳实践

1. **日志命名**：使用有意义的名称（如 `model_epochs_date.log`）
2. **磁盘空间**：长时间训练的日志文件可能很大，注意磁盘空间
3. **GPU 监控**：即使后台运行，也可以通过 `jtop` 或 `tegrastats` 监控 GPU 使用情况
4. **性能模式**：训练前确认已开启 MAXN_SUPER 模式
