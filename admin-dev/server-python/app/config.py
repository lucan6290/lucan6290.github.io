"""
博客管理后台 - 配置
"""
from __future__ import annotations

from pathlib import Path
from typing import List

# ============================================================
# 博客路径
# ============================================================

BLOG_ROOT = Path(r"E:\A-Code\blog")
POSTS_DIR = BLOG_ROOT / "source" / "_posts"

# ============================================================
# 分类前缀映射（与 scripts/new-post.js 保持同步）
# ============================================================

PREFIX_TO_DIR: dict = {
    "ts": {"dir": "tech-study", "category": "技术研习", "cover": "/img/covers/tech-study.svg"},
    "pr": {"dir": "pitfall-review", "category": "踩坑复盘", "cover": "/img/covers/pitfall-review.svg"},
    "pp": {"dir": "project-practice", "category": "项目实战", "cover": "/img/covers/project-practice.svg"},
    "ge": {"dir": "growth-essay", "category": "成长随笔", "cover": "/img/covers/growth-essay.svg"},
    "rs": {"dir": "resource-sharing", "category": "资源分享", "cover": "/img/covers/resource-sharing.svg"},
}

# ============================================================
# 服务器配置
# ============================================================

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 15000

# CORS 允许的来源
CORS_ORIGINS: List[str] = [
    "http://localhost:4000",
    "http://localhost:14000",
    "http://localhost:3000",
]

# ============================================================
# AI 模型预设
# ============================================================

MODEL_PRESETS: List[dict] = [
    {
        "id": "deepseek",
        "name": "深度求索 (DeepSeek)",
        "baseUrl": "https://api.deepseek.com/v1",
        "modelId": "deepseek-chat",
    },
    {
        "id": "qwen",
        "name": "通义千问 (Qwen)",
        "baseUrl": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "modelId": "qwen-plus",
    },
    {
        "id": "glm",
        "name": "智谱AI (GLM)",
        "baseUrl": "https://open.bigmodel.cn/api/paas/v4",
        "modelId": "glm-4-flash",
    },
    {
        "id": "kimi",
        "name": "月之暗面 (Kimi)",
        "baseUrl": "https://api.moonshot.cn/v1",
        "modelId": "moonshot-v1-8k",
    },
    {
        "id": "mimo",
        "name": "小米 (MiMo)",
        "baseUrl": "https://platform.xiaomimimo.com",
        "modelId": "mimo",
    },
]
