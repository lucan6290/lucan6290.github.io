---
title: "Jetson Orin NANO 常见错误解决笔记"
date: 2025-01-20 10:00:00
categories:
  - [技术研习, Jetson_Orin_NANO]
tags: [jetson, orin-nano, bug, 错误解决, docker, nvidia, rsync, 排错, 踩坑]
series: "Jetson Orin NANO 开发板使用笔记"
series_order: 18
description: 记录 Jetson Orin NANO 使用过程中遇到的常见错误及解决方案，包括 Docker 源配置、NVIDIA TLS 握手错误、Rsync 权限问题。
cover: /img/covers/tech-study.svg
slug: ts-jetson-common-errors
status: published
lang: zh-CN
---

## 前言

使用 Jetson Orin NANO 开发板的过程中，难免会遇到各种配置和环境问题。本文记录了几个常见错误及其解决方案。

---

## 一、Docker 软件源配置错误

### 问题描述

```bash
$ sudo apt update
E: Malformed entry 1 in list file /etc/apt/sources.list.d/docker.list (URI)
E: The list of sources could not be read.
```

### 问题分析

- **控制字符问题**：第一行末尾有异常字符
- **格式错误**：文件被分成了多行，正确格式应该是一行

### 解决方案

```bash
# 删除有问题的文件
sudo rm /etc/apt/sources.list.d/docker.list

# 重新创建（单行格式）
echo "deb [arch=arm64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://mirrors.tuna.tsinghua.edu.cn/docker-ce/linux/ubuntu jammy stable" | sudo tee /etc/apt/sources.list.d/docker.list
```

---
{% asset_img 'ts-jetson-常见错误解决笔记-img1.png' 'Docker 源配置错误解决' %}

## 二、NVIDIA 软件源 TLS 握手错误

### 问题描述

```bash
$ sudo apt update
Err:1 https://repo.download.nvidia.com/jetson/common r36.4 InRelease
  Could not handshake: The TLS connection was non-properly terminated.
```

### 问题原因

- **网络环境问题**：TLS 连接被异常终止，通常与防火墙或代理设置有关
- **服务器问题**：NVIDIA 服务器暂时性问题

### 解决方案

**方法一：将 HTTPS 改为 HTTP 协议**

```bash
# 查找 NVIDIA 源配置文件
ls /etc/apt/sources.list.d/ | grep -i nvidia

# 将所有 NVIDIA 源从 HTTPS 改为 HTTP
sudo sed -i 's|https://|http://|g' /etc/apt/sources.list.d/nvidia-l4t-apt-source.list

# 重新更新
sudo apt update
```

**方法二：配置代理服务器**

如果有代理服务器，可以配置 apt 使用代理。

{% asset_img 'ts-jetson-常见错误解决笔记-img2.png' 'NVIDIA TLS 握手错误解决' %}
---

## 三、Rsync 上传权限问题

### 问题描述

```
无法传输文件夹 'model.pth'
Unknown message with code "rsync 失败，退出代码为: 23"
```

### 问题分析

1. **SSH 密钥存储问题**：`Could not create directory '/home/lucan/.ssh'`
2. **权限拒绝错误**：rsync 在目标服务器上没有写入权限，错误代码 23 表示权限问题

### 解决方案

**修复目标目录权限（推荐）**

在 Jetson 设备上执行：

```bash
# 确保目标目录存在并设置正确权限
sudo mkdir -p /home/jetson/lucan/code/RNN
sudo chown -R jetson:jetson /home/jetson/lucan/code/RNN
sudo chmod 755 /home/jetson/lucan/code/RNN
```

**检查目标服务器状态**

```bash
# 检查目录权限
ls -la /home/jetson/lucan/code/

# 检查磁盘空间
df -h

# 检查用户权限
id jetson
```

---

## 四、总结

| 错误类型 | 常见原因 | 解决方案 |
|---------|---------|---------|
| Docker 源配置错误 | 配置文件格式问题 | 重新创建正确格式的配置文件 |
| NVIDIA TLS 错误 | 网络环境问题 | 改为 HTTP 协议 |
| Rsync 权限问题 | 目标目录权限不足 | 设置正确的用户和权限 |

建议定期备份重要配置，遇到问题时先查看日志信息定位具体原因。
