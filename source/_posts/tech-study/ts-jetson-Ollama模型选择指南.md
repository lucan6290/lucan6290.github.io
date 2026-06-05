---
title: "Ollama 模型选择指南（Jetson 适配）"
date: 2025-12-20 10:00:00
categories:
  - [技术研习, 系列专题]
tags: [jetson, orin-nano, ollama, llm, 大模型, 模型选择, deepseek, qwen, llama]
series: "Jetson Orin NANO 开发板使用笔记"
series_order: 13
description: 针对 Jetson Orin NANO 8GB 内存的 Ollama 模型选择指南，涵盖通用文本、代码专用、多模态等模型的详细对比与推荐。
cover: /img/covers/tech-study.svg
slug: ts-jetson-ollama-model-guide
status: published
lang: zh-CN
---

## 前言

Ollama 支持众多开源大语言模型，但在 Jetson Orin NANO 的 8GB 内存限制下，模型选择至关重要。本文整理了适合 Jetson 设备的模型库一览表。

---

## 一、完整模型一览表

| 模型名称 | 开发者 | 特点 | 适合工作 | 模型大小 | 类型 |
|---------|--------|------|---------|----------|------|
| **deepseek-r1:7b** | 深度求索 | 推理能力强，数学代码突出，128K 上下文 | 复杂推理、代码生成、日常对话 | 4.7GB | 文本 |
| **llama3:8b** | Meta | 综合能力强，多语言支持 | 通用对话、内容创作 | 4.7GB | 文本 |
| **qwen2:7b** | 阿里巴巴 | 中文能力强，多语言支持 | 中文对话、创作 | 4.4GB | 文本 |
| **deepseek-coder:6.7b** | 深度求索 | 代码生成专用 | 代码生成、bug 修复 | 3.8GB | 代码 |
| **codellama:7b** | Meta | 基于 Llama 2 的代码模型 | 代码生成、解释 | 3.8GB | 代码 |
| **starcoder2:7b** | Hugging Face | BigCode 项目 | 大规模代码生成 | 4.0GB | 代码 |
| **phi3:3.8b** | 微软 | 小参数高性能 | 资源受限环境 | 2.2GB | 文本 |
| **phi3:mini** | 微软 | 轻量级、高性能 | 快速响应场景 | 2.2GB | 文本 |
| **tinyllama:1.1b** | 社区 | 极致轻量 | 快速原型、简单对话 | 637MB | 文本 |
| **llava:7b** | 威斯康星大学 | 图像理解 | 图像描述、图文问答 | 4.7GB | 多模态 |
| **llava-phi3:3.8b** | 威斯康星大学 | 轻量级视觉语言 | 轻量级视觉任务 | 2.9GB | 多模态 |
| **gemma:7b** | Google | 基于 Gemini 技术 | 研究、实验 | 5.0GB | 文本 |
| **orca-mini:3b** | 微软 | 轻量级教学模型 | 教育场景 | 2.0GB | 文本 |

---

## 二、按类型分类

### 通用文本模型

| 模型 | 大小 | 最佳场景 | 内存要求 |
|------|------|---------|---------|
| deepseek-r1:7b | 4.7GB | 综合能力强 | >8GB |
| llama3:8b | 4.7GB | 多语言对话 | >8GB |
| qwen2:7b | 4.4GB | 中文场景 | >8GB |
| phi3:3.8b | 2.2GB | 平衡性能 | 4-8GB |
| tinyllama:1.1b | 637MB | 快速测试 | <4GB |

### 代码专用模型

| 模型 | 大小 | 最佳场景 | 语言支持 |
|------|------|---------|---------|
| deepseek-coder:6.7b | 3.8GB | 代码生成、bug 修复 | Python, JS, Java, C++ |
| codellama:7b | 3.8GB | 代码生成、解释 | 多种主流语言 |
| starcoder2:7b | 4.0GB | 大规模代码生成 | 覆盖广泛 |

### 多模态模型

| 模型 | 大小 | 最佳场景 | 视觉能力 |
|------|------|---------|---------|
| llava:7b | 4.7GB | 图像描述、视觉问答 | 强 |
| llava-phi3:3.8b | 2.9GB | 轻量级视觉任务 | 适中 |

---

## 三、快速选择指南

### 按需求选择

| 需求 | 推荐模型 |
|------|---------|
| 日常对话 | `phi3:3.8b`（平衡）或 `deepseek-r1:7b`（最强） |
| 中文场景 | `qwen2:7b` 或 `deepseek-r1:7b` |
| 编程开发 | `deepseek-coder:6.7b` |
| 图像理解 | `llava-phi3:3.8b`（轻量）或 `llava:7b`（完整） |
| 快速测试 | `tinyllama:1.1b` 或 `phi3:mini` |
| 教育场景 | `orca-mini:3b` 或 `phi3:mini` |

### 按内存选择

| 内存 | 推荐模型 |
|------|---------|
| <4GB | `tinyllama:1.1b`、`phi3:mini` |
| 4-8GB | `phi3:3.8b`、`llava-phi3:3.8b`、`orca-mini:3b` |
| >8GB | `deepseek-r1:7b`、`llama3:8b`、`deepseek-coder:6.7b` |

---

## 四、管理命令参考

```bash
ollama run <模型名称>          # 运行模型
ollama list                    # 查看所有模型
ollama rm <模型名称>           # 删除模型
ollama cp <源> <目标>          # 复制/创建别名
```

---

## 五、使用建议

1. **测试阶段**：先用轻量级模型（如 `tinyllama:1.1b`）验证功能
2. **生产环境**：根据任务选择专用模型
3. **中文用户**：优先考虑 `qwen2:7b` 或 `deepseek-r1:7b`
4. **Jetson 设备**：注意内存限制，避免同时运行多个大模型
