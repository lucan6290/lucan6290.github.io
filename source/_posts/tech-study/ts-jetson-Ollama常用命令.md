---
title: "Ollama 常用命令参考"
date: 2025-12-13 10:00:00
categories:
  - [技术研习, 系列专题]
tags: [jetson, orin-nano, ollama, llm, 命令参考, 端口配置]
series: "Jetson Orin NANO 开发板使用笔记"
series_order: 12
description: Ollama 在 Jetson Orin Nano 上的完整操作命令大全，涵盖核心使用、模型管理、服务管理、网络配置与故障排查。
cover: /img/covers/tech-study.svg
slug: ts-jetson-ollama-commands
status: published
lang: zh-CN
---

## 前言

本文整理了 Ollama 在 Jetson Orin Nano 上的所有常用命令，从基础使用到高级配置，方便日常查阅。

---

## 一、核心使用命令

### 运行模型对话

```bash
ollama run <模型名>
ollama run deepseek-r1:7b
ollama run phi3:mini
```

### 拉取模型

```bash
ollama pull <模型名>
ollama pull deepseek-r1:7b
ollama pull llama3.2:3b
```

### 列出已安装模型

```bash
ollama list
```

---

## 二、模型管理命令

```bash
# 查看运行中的模型
ollama ps

# 停止运行中的模型
ollama stop deepseek-r1:7b

# 删除模型
ollama rm deepseek-r1:7b

# 复制/重命名模型
ollama cp deepseek-r1:7b deepseek-r1:7b-backup

# 显示模型详细信息
ollama show deepseek-r1:7b

# 导出模型信息
ollama show deepseek-r1:7b --modelfile
```

---

## 三、服务管理命令

```bash
sudo systemctl stop ollama      # 停止服务
sudo systemctl restart ollama   # 重启服务
sudo systemctl start ollama     # 启动服务
sudo systemctl status ollama    # 查看状态
sudo systemctl daemon-reload    # 重载配置
```

---

## 四、网络与端口配置

### 默认端口分配

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| 监听地址 | `127.0.0.1` | 仅本机可访问 |
| 默认端口 | `11434` | Ollama 服务默认端口 |

### 端口配置方法

**方法一：systemd 配置（推荐，持久化）**

```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d/
sudo vim /etc/systemd/system/ollama.service.d/override.conf
```

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
Environment="OLLAMA_PORT=8080"
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

**方法二：systemctl 临时设置**

```bash
sudo systemctl set-environment OLLAMA_HOST=0.0.0.0
sudo systemctl restart ollama
```

### 防火墙配置

```bash
sudo ufw allow 11434/tcp
sudo ufw reload
sudo ufw status
```

### 访问测试

```bash
# 本机测试
curl http://127.0.0.1:11434/

# 局域网测试
curl http://192.168.31.155:11434/

# 检查端口占用
sudo netstat -tlnp | grep 11434
```

---

## 五、系统性能优化

```bash
# 切换到高性能模式
sudo nvpmodel -m 2

# 设置最大时钟频率
sudo jetson_clocks

# 查看当前电源模式
sudo nvpmodel -q

# 查看系统温度和频率
jtop
sudo tegrastats
```

---

## 六、安装与卸载

```bash
# 一键安装
curl -fsSL https://ollama.com/install.sh | sh

# 卸载
sudo apt remove ollama
sudo apt remove --purge ollama
```

---

## 七、故障排查

```bash
# 查看实时日志
sudo journalctl -u ollama -f

# 查看 Ollama 进程
ps aux | grep ollama

# 检查端口占用
sudo netstat -tlnp | grep 11434

# 检查磁盘空间
df -h
du -sh ~/.ollama/
```

---

## 八、常用模型推荐（8GB Jetson）

| 场景 | 推荐模型 |
|------|---------|
| 轻量级测试 | `phi3:mini`、`llama3.2:3b` |
| 平衡性能 | `qwen:7b`、`llama3.2:7b` |
| 推理能力 | `deepseek-r1:7b` |

---

## 九、安全建议

1. 不要将 Ollama 暴露到公网（默认无认证）
2. 仅开放必要端口
3. 建议设置监听地址为特定 IP 而非 `0.0.0.0`
4. 在路由器层面设置访问控制
