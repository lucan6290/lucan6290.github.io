---
title: "Ollama 部署 LLM —— 开放局域网访问"
date: 2025-12-03 10:00:00
categories:
  - [技术研习, Jetson_Orin_NANO]
tags: [jetson, orin-nano, ollama, llm, 大模型, 局域网, deepseek, open-webui]
series: "Jetson Orin NANO 开发板使用笔记"
series_order: 10
description: 在 Jetson Orin NANO 上安装 Ollama 并部署大语言模型，配置局域网访问，使用 LangChain 调用，以及部署 Open WebUI。
cover: /img/covers/tech-study.svg
slug: ts-jetson-ollama-deploy
status: published
lang: zh-CN
---

## 前言

Ollama 是当前在 Jetson 上运行大语言模型最便捷的工具之一，它自带 CUDA 支持，可以省去很多环境配置的麻烦。本文记录在 Jetson Orin NANO 上安装 Ollama、部署模型、开放局域网访问的完整流程。

---

## 一、安装 Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

安装完成后，Ollama 会自动创建一个服务并在后台运行。

{% asset_img 'ts-jetson-Ollama部署LLM-img1.png' 'Ollama 安装信息' %}

### 验证安装

```bash
ollama run phi3:mini
```

如果模型开始下载并能够进行对话，说明 Ollama 已成功安装。

{% asset_img 'ts-jetson-Ollama部署LLM-img2.png' 'Ollama 验证安装' %}

---

## 二、部署大模型

对于 8GB 内存的 Jetson Orin Nano，建议选择参数量在 7B 或 8B 及以下的模型：

```bash
# 拉取模型
ollama pull deepseek-r1:7b

# 运行模型
ollama run deepseek-r1:7b
```

{% asset_img 'ts-jetson-Ollama部署LLM-img3.png' '部署 DeepSeek 模型' %}

---

## 三、开放局域网访问

默认情况下，Ollama 服务只监听本机（`127.0.0.1`）。需要配置监听所有网络接口。

### 1. 配置 Ollama 监听地址

```bash
sudo systemctl stop ollama

sudo mkdir -p /etc/systemd/system/ollama.service.d/
sudo vim /etc/systemd/system/ollama.service.d/environment.conf
```

添加以下内容：

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
```

### 2. 重启 Ollama 服务

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### 3. 调整防火墙规则（可选）

```bash
sudo ufw allow 11434/tcp
sudo ufw reload
```

---

## 四、验证局域网访问

```bash
# 查看 Jetson 的 IP 地址
ip addr show
```

在局域网其他设备的浏览器中访问：

```
http://<Jetson的IP>:11434/
```

如果页面显示 "Ollama is running"，局域网访问已成功！

{% asset_img 'ts-jetson-Ollama部署LLM-img4.png' '局域网访问成功' %}

---

## 五、使用 LangChain 调用

在局域网内的电脑上通过 Python 调用 Jetson 上的模型：

```python
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="deepseek-r1:7b",
    base_url="http://192.168.31.155:11434",
    temperature=0.7,
    streaming=True,
    verbose=True,
)

if __name__ == '__main__':
    messages = [
        ("system", "你是一个有帮助的AI助手。请用简洁清晰的方式回答问题。"),
        ("human", "请用简单的语言解释一下什么是人工智能。"),
    ]
    ai_msg = llm.invoke(messages)
    print(ai_msg.content)
```

{% asset_img 'ts-jetson-Ollama部署LLM-img6.png' 'LangChain 调用结果' %}

---

## 六、部署 Open WebUI（可选）

通过 Docker 部署 Web 界面，方便在浏览器中与模型交互：

```bash
docker run -d \
  --network=host \
  -v open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://127.0.0.1:11434 \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

访问 `http://<Jetson的IP>:8080` 即可使用 Web 界面。
{% asset_img 'ts-jetson-Ollama部署LLM-img5.png' 'Open WebUI 部署成功' %}

---

## 七、注意事项

- **模型选择**：8GB 内存运行 7B 模型会较紧张，可尝试 3B 模型如 `llama3.2:3b`
- **性能模式**：建议切换到 MAXN_SUPER 高性能模式以获得更好的推理速度
