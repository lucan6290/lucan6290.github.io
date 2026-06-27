---
title: "Conda 常用命令参考"
date: 2025-10-25 10:00:00
categories:
  - [技术研习, Jetson_Orin_NANO]
tags: [jetson, orin-nano, conda, python, 包管理, 命令参考]
series: "Jetson Orin NANO 开发板使用笔记"
series_order: 5
description: Jetson Orin NANO 上常用的 Conda 环境管理与包管理命令速查手册。
cover: /img/covers/tech-study.svg
slug: ts-jetson-conda-commands
status: published
lang: zh-CN
---

## 前言

在 Jetson Orin NANO 上使用 Miniforge 管理 Python 环境时，Conda 是最常用的工具。本文整理了日常开发中最常用的 Conda 命令，方便快速查阅。

---

## 一、环境管理

```bash
# 创建新环境
conda create -n myenv python=3.10

# 激活环境
conda activate myenv

# 退出当前环境
conda deactivate

# 列出所有环境
conda env list

# 删除环境
conda remove -n myenv --all

# 重命名环境
conda rename -n 旧名称 新名称

# 克隆现有环境为新环境
conda create --name 新环境名 --clone 源环境名
```

---

## 二、包管理

```bash
# 安装包
conda install package_name

# 安装指定版本
conda install package_name=1.2.3

# 列出当前环境的包
conda list

# 搜索包
conda search package_name

# 移除包
conda remove package_name

# 更新所有包
conda update --all

# 更新指定包
conda update package_name
```

---

## 三、信息查询

```bash
# 查看 conda 系统信息
conda info

# 显示当前配置
conda config --show

# 查看频道列表
conda config --show channels
```

---

## 四、常用技巧

```bash
# 在指定环境中安装包（不切换环境）
conda install -n myenv package_name

# 导出环境配置
conda env export > environment.yml

# 从配置文件创建环境
conda env create -f environment.yml

# 清理缓存
conda clean --all
```
