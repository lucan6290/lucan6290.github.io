---
title: Agent 入门笔记 —— 从概念到实战
date: 2026-05-20 10:00:00
categories:
  - [技术研习, AI 探索]
tags: [ai-agent, llm, tutorial, note, learning-process, AI, 人工智能]
description: 系统学习 AI Agent 的笔记，涵盖概念、架构、核心组件和实践经验。
cover: /img/covers/tech-study.svg
---

## 什么是 Agent？

Agent（智能体）是能够自主感知环境、做出决策并执行动作的 AI 系统。与传统的单次问答不同，Agent 具备以下核心能力：

```
用户提问 → Agent 规划 → 调用工具 → 观察结果 → 反思调整 → 输出结果
```

简单来说：**LLM 是大脑，Agent 是能动手的大脑**。

## Agent 的核心架构

一个典型的 Agent 包含以下几个关键组件：

| 组件 | 作用 | 例子 |
|------|------|------|
| **LLM** | 推理与规划 | GPT-4、Claude |
| **Memory** | 记忆与上下文 | 短期记忆、长期记忆 |
| **Tools** | 能力扩展 | 搜索、代码执行、API 调用 |
| **Planning** | 任务分解 | ReAct、Plan-and-Execute |

### ReAct 模式

目前最流行的 Agent 推理模式是 **ReAct（Reasoning + Acting）**：

```
Thought: 我需要知道今天的天气才能决定穿什么
Action: search_weather("北京")
Observation: 北京今天晴，18-28°C
Thought: 天气不错，建议穿薄外套
Answer: 今天北京晴天，18-28°C，建议穿薄外套出门
```

## 动手实践：构建一个简单的 Agent

用一个简单的例子来理解 Agent 的工作原理：

```python
import openai

class SimpleAgent:
    def __init__(self, api_key):
        self.client = openai.OpenAI(api_key=api_key)
        self.tools = {
            "calculator": self.calculate,
            "search": self.search_web
        }
        self.memory = []  # 短期记忆
    
    def calculate(self, expression):
        """简单的计算器工具"""
        try:
            return str(eval(expression))
        except:
            return "计算错误"
    
    def search_web(self, query):
        """模拟搜索（实际应接入搜索 API）"""
        return f"关于「{query}」的搜索结果..."
    
    def run(self, user_input):
        # 构建 prompt
        prompt = f"""
用户问题：{user_input}
历史对话：{self.memory[-5:] if self.memory else '无'}

你可以使用以下工具：calculator, search
如果需要使用工具，请用格式：TOOL: tool_name(arg)
如果需要直接回答：ANSWER: 你的回答
"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = response.choices[0].message.content
        
        # 解析 Agent 输出
        if result.startswith("TOOL:"):
            tool_call = result[5:].strip()
            # 执行工具调用...
            # 将结果反馈给 LLM 继续推理
            return self.execute_tool(tool_call)
        else:
            self.memory.append(result)
            return result
```

## Agent 的常见类型

### 1. 单 Agent 系统
- 一个 LLM 完成所有任务
- 适合简单任务
- 例如：个人助手、代码审查

### 2. 多 Agent 协作
- 多个 Agent 分工协作
- 适合复杂场景
- 例如：软件开发团队（CEO + CTO + 程序员 + 测试）

### 3. Agent + RAG
- Agent 结合知识库检索
- 适合需要专业知识的场景
- 例如：法律咨询、医疗问诊

## 学习资源推荐

{% note info %}
以下是 Agent 学习的推荐路径：
1. 先理解 ReAct 论文
2. 阅读 LangChain 文档
3. 动手实现一个简单 Agent
4. 研究 AutoGPT / MetaGPT 等开源项目
{% endnote %}

## 总结

Agent 是 AI 从「对话」走向「行动」的关键一步。学习 Agent，本质上是在学习如何让 AI 更好地使用工具、规划任务、与环境交互。

对于求职来说，Agent 也是一个很好的技术亮点。后续我会继续深入 Agent 的学习，并在这里记录过程。

---
*每一次探索，都是成长*