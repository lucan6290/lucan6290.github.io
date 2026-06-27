---
title: "Docker 常用命令参考"
date: 2025-11-25 10:00:00
categories:
  - [技术研习, Jetson_Orin_NANO]
tags: [jetson, orin-nano, docker, 容器, 命令参考, 网络配置]
series: "Jetson Orin NANO 开发板使用笔记"
series_order: 9
description: Jetson Orin NANO 上 Docker 常用命令完整参考，涵盖参数详解、网络配置、端口映射、数据持久化与重启策略。
cover: /img/covers/tech-study.svg
slug: ts-jetson-docker-commands
status: published
lang: zh-CN
---

## 前言

Docker 是 Jetson Orin NANO 上部署应用的重要工具。本文整理了 Docker 的常用命令，涵盖从基础操作到网络配置、数据持久化的完整参考。

---

## 一、基础参数详解

| 参数 | 说明 | 示例 |
|------|------|------|
| `-i` | 保持 STDIN 打开 | `docker run -i` |
| `-t` | 分配伪 TTY 终端 | `docker run -t` |
| `-d` | 后台运行（守护进程模式） | `docker run -d` |
| `-p` | 端口映射 | `docker run -p 8080:80` |
| `-v` | 挂载卷（数据持久化） | `docker run -v /host:/container` |
| `-e` | 设置环境变量 | `docker run -e KEY=value` |
| `--name` | 指定容器名称 | `docker run --name my-container` |
| `--network` | 指定网络模式 | `docker run --network host` |
| `--restart` | 重启策略 | `docker run --restart always` |
| `--rm` | 停止后自动删除 | `docker run --rm` |

---

## 二、查看与拉取

```bash
# 查看版本
docker --version

# 查看详细信息
docker info

# 拉取镜像
docker pull <image_name>
docker pull <image_name>:<tag>
docker pull ubuntu:18.04
```

---

## 三、运行容器

```bash
# 基本运行
docker run <image_name>

# 交互模式运行（输入 exit 退出）
docker run -it <image_name>:<tag> /bin/bash

# 查看正在运行的容器
docker ps

# 查看所有容器（含已停止）
docker ps -a
```

---

## 四、网络与端口配置

### 端口映射

```bash
# 基本格式：宿主机端口:容器端口
docker run -p 8080:80 nginx

# 多端口映射
docker run -d -p 80:80 -p 443:443 -p 8080:8080 nginx

# 查看容器端口映射
docker port <container_name>

# 格式化查看所有容器端口
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Ports}}"
```

### 局域网访问配置

要让局域网内其他设备访问 Docker 容器服务：

```bash
# 方式1：Host 网络模式（推荐）
docker run -d --network host --name my-app my-image

# 方式2：绑定到所有网络接口
docker run -d -p 0.0.0.0:8080:8080 --name my-app my-image
```

**配置要点**：
1. 使用 `0.0.0.0:<port>` 而不是仅 `<port>`
2. 确保防火墙允许对应端口
3. 查看本机局域网 IP：`ifconfig`

### 网络模式

```bash
docker run --network bridge   # 默认桥接模式
docker run --network host     # 主机网络模式（与宿主机共享）
docker run --network none     # 无网络连接
docker run --network my-network  # 自定义网络
```

---

## 五、数据持久化

```bash
# 基本挂载
docker run -v /host/path:/container/path

# 只读挂载
docker run -v /host/path:/container/path:ro

# 命名卷
docker run -v my-volume:/data
```

---

## 六、重启策略

| 策略 | 说明 | 场景 |
|------|------|------|
| `--restart=no` | 不自动重启（默认） | 开发测试 |
| `--restart=on-failure` | 异常退出时重启 | 有状态应用 |
| `--restart=on-failure:N` | 最多重启 N 次 | 故障恢复 |
| `--restart=always` | 始终自动重启 | 关键服务 |
| `--restart=unless-stopped` | 除非手动停止，否则一直重启 | 长期运行服务 |

---

## 七、资源限制

```bash
# 内存限制
docker run -m 512m nginx

# CPU 限制
docker run --cpus=1.0 nginx

# 组合限制
docker run -m 1g --cpus=2 nginx

# 详细资源查看
docker stats
```

---

## 八、完整部署示例：Open WebUI

```bash
docker run -d \
  --network=host \
  -v open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://127.0.0.1:11434 \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

**部署后验证：**

```bash
docker ps
docker logs open-webui
curl http://localhost:3001
```

---

## 九、容器管理

```bash
# 停止容器
docker stop <container_id>

# 进入正在运行的容器
docker exec -it <container_id> /bin/bash

# 提交容器为镜像
docker commit <container_id> <image_name>:<tag>

# 清理已停止的容器
docker container prune

# 删除镜像（需先停止并清理）
docker rmi <image_name>:<tag>
```

---

## 十、参数组合示例

```bash
# 完整配置
docker run -d \
  --name my-app \
  -p 8080:80 \
  -v /data:/app/data \
  -e ENV=production \
  -m 512m \
  --cpus=1.0 \
  --restart always \
  --network host \
  my-image:latest

# 快速开发启动
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  ubuntu:latest /bin/bash
```
