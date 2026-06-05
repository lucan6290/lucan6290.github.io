---
title: "Jetson Orin NANO 完整换源操作指南"
date: 2025-10-15 10:00:00
categories:
  - [技术研习, 系列专题]
tags: [jetson, orin-nano, apt, 换源, Linux, 环境配置, pip, conda, docker]
series: "Jetson Orin NANO 开发板使用笔记"
series_order: 3
description: Jetson Orin NANO 完整换源指南，涵盖 APT、Conda、Pip、ROS 2、Docker 镜像源的更换与配置。
cover: /img/covers/tech-study.svg
slug: ts-jetson-source-mirror
status: published
lang: zh-CN
---

## 前言

国内使用 Jetson Orin NANO 开发板，默认的软件源访问速度较慢，甚至可能无法连接。本文提供一套完整的换源方案，覆盖 APT、Conda、Pip、ROS 2、Docker 等所有常用源。

---

## 一、更换 APT 源（系统级软件包）

### 备份原始源

```bash
sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak
```

### 打开并编辑源文件

```bash
# 使用 nano 编辑器（推荐新手）
sudo nano /etc/apt/sources.list

# 或者使用 vim
sudo vim /etc/apt/sources.list
```

### 替换文件内容

删除原文件所有内容，替换为以下**清华源**配置：

```bash
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ jammy main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ jammy-security main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ jammy-updates main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ jammy-backports main restricted universe multiverse
```

### 保存并退出

- **nano 编辑器**：按 `Ctrl + X`，然后按 `Y` 确认保存，最后按 `Enter` 确认文件名
- **vim 编辑器**：按 `Esc`，然后输入 `:wq` 保存并退出

### 更新软件列表

```bash
sudo apt update
```

---

## 二、配置 Conda 源

### 打开 Conda 配置文件

```bash
nano ~/.condarc

# 如果文件不存在，先创建
touch ~/.condarc
nano ~/.condarc
```

### 写入配置内容

```yaml
channels:
  - defaults
show_channel_urls: true
default_channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/msys2
custom_channels:
  conda-forge: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  msys2: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  bioconda: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  menpo: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  pytorch: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  pytorch-lts: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  simpleitk: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  nvidia: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
```

### 保存并验证

```bash
# 清除 conda 缓存
conda clean -i

# 验证配置
conda config --show
```

---

## 三、配置 ROS 2 Humble 源

### 打开 ROS 2 源文件

```bash
# 查看现有的 ROS 源文件
ls /etc/apt/sources.list.d/

# 打开 ROS 2 源文件进行编辑
sudo nano /etc/apt/sources.list.d/ros2.list
```

### 替换文件内容

使用华中科技大学镜像：

```bash
deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] https://mirrors.hust.edu.cn/ros2/ubuntu jammy main
```

或者使用清华源：

```bash
deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] https://mirrors.tuna.tsinghua.edu.cn/ros2/ubuntu jammy main
```

### 保存并更新

```bash
sudo apt update
```

---

## 四、配置 Pip 源

### 方法一：使用命令设置（推荐）

```bash
# 设置全局 pip 源（清华源）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 添加信任主机
pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn
```

### 方法二：手动编辑配置文件

```bash
mkdir -p ~/.pip
nano ~/.pip/pip.conf
```

写入以下内容：

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
timeout = 120
```

---

## 五、配置 Docker 镜像源

### 打开 Docker 配置

```bash
sudo mkdir -p /etc/docker
sudo nano /etc/docker/daemon.json
```

### 添加镜像配置

```json
{
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  },
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baiduce.com"
  ]
}
```

### 重启 Docker 服务

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

---

## 六、验证换源结果

```bash
# 检查 APT 源
sudo apt update
apt-cache policy

# 检查 Conda 源
conda config --show channels

# 检查 Pip 源
pip config list

# 测试下载速度
time pip install numpy
```

---

## 七、遇到问题时恢复备份

```bash
# 恢复 APT 源备份
sudo cp /etc/apt/sources.list.bak /etc/apt/sources.list
sudo apt update

# 删除 Conda 配置（恢复默认）
rm ~/.condarc

# 删除 Pip 配置
rm ~/.pip/pip.conf
```

---

## 八、换源完成后的操作

```bash
# 全面更新系统
sudo apt update
sudo apt upgrade

# 清理不必要的包
sudo apt autoremove

# 更新 conda
conda update conda
conda update --all
```
