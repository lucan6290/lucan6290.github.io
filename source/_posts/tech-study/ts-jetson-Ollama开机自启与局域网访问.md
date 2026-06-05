---
title: "Ollama 开机自启与局域网访问配置"
date: 2025-12-08 10:00:00
categories:
  - [技术研习, 系列专题]
tags: [jetson, orin-nano, ollama, systemd, 开机自启, 局域网, 部署运维]
series: "Jetson Orin NANO 开发板使用笔记"
series_order: 11
description: 配置 Jetson Orin NANO 上的 Ollama 服务实现开机自动启动、自动预加载模型，并支持局域网持久访问。
cover: /img/covers/tech-study.svg
slug: ts-jetson-ollama-autostart
status: published
lang: zh-CN
---

## 前言

将 Ollama 配置为开机自动启动，并预加载指定模型，是实现 Jetson 作为"本地大模型服务器"的关键步骤。本文详细介绍完整的配置流程。

---

## 一、配置网络监听地址和端口

默认情况下，Ollama 仅监听 `127.0.0.1:11434`。需修改为局域网可访问。

### 1. 编辑环境配置文件

```bash
sudo systemctl stop ollama
sudo mkdir -p /etc/systemd/system/ollama.service.d/
sudo vim /etc/systemd/system/ollama.service.d/environment.conf
```

### 2. 添加监听配置

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

**配置说明**：
- `0.0.0.0`：监听所有网络接口（推荐，最灵活）
- `192.168.x.x`：监听特定 IP 地址
- `127.0.0.1`：仅本地访问

> `[Service]` 是 systemd 服务配置的段落标识，`Environment=` 用于为服务进程设置环境变量。

---

## 二、配置模型自动加载

### 1. 创建预加载配置文件

```bash
sudo vim /etc/systemd/system/ollama.service.d/preload-model.conf
```

### 2. 添加预加载命令

```ini
[Service]
# 使用 run 命令配合 timeout 防止阻塞
ExecStartPost=/usr/bin/timeout 30 /usr/local/bin/ollama run deepseek-r1:7b
```

---

## 三、应用配置并重启服务

```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 重启 Ollama 服务
sudo systemctl restart ollama

# 设置开机自启
sudo systemctl enable ollama
```

---

## 四、验证配置

```bash
# 检查服务状态
sudo systemctl status ollama

# 检查网络监听
sudo netstat -tlnp | grep ollama

# 检查模型列表
ollama list

# 测试 API 访问
curl http://127.0.0.1:11434/api/tags

# 局域网测试（从其他电脑）
curl http://192.168.31.155:11434/api/tags
```

---

## 五、防火墙配置

```bash
# 检查防火墙状态
sudo ufw status

# 开放 Ollama 端口
sudo ufw allow 11434/tcp
sudo ufw reload
```

---

## 六、故障排除

### 服务启动失败

```bash
sudo journalctl -u ollama -f --no-pager
```

### 模型未加载

```bash
ollama pull deepseek-r1:7b
ollama list
```

### 无法从局域网访问

```bash
# 检查端口监听状态
sudo ss -tlnp | grep 11434

# 临时关闭防火墙测试
sudo ufw disable
# 测试完成后恢复
sudo ufw enable
```

---

## 七、高级配置

### 配置多个模型预加载

```ini
[Service]
ExecStartPost=/usr/bin/bash -c "/usr/bin/ollama pull deepseek-r1:7b && /usr/bin/ollama pull llama2:7b"
```

### 修改模型存储路径

```bash
sudo vim /etc/default/ollama
# 添加
OLLAMA_MODELS=/path/to/your/models
```

### Jetson 性能优化参数

```bash
sudo vim /etc/default/ollama
# 添加
OLLAMA_NUM_PARALLEL=2
OLLAMA_MAX_LOADED_MODELS=1
```

---

## 八、调用示例

### Python（LangChain）

```python
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="deepseek-r1:7b",
    base_url="http://192.168.31.155:11434",
    temperature=0.7,
)

response = llm.invoke("你好，请介绍一下你自己。")
print(response.content)
```

### HTTP API

```bash
curl http://192.168.31.155:11434/api/generate \
  -d '{
    "model": "deepseek-r1:7b",
    "prompt": "请用中文回答：什么是人工智能？",
    "stream": false
  }'
```

---

## 九、注意事项

1. **安全提醒**：`OLLAMA_HOST=0.0.0.0` 会使服务对整个局域网开放，请确保在可信网络中使用
2. **性能考虑**：Jetson 内存有限，不要同时加载过多大型模型
3. **存储空间**：7B 参数模型通常需要 4-8GB 存储空间
