from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    admin_root: Path
    backend_root: Path
    blog_root: Path
    posts_dir: Path
    category_registry_path: Path
    cache_dir: Path
    server_host: str
    server_port: int
    cors_origins: list[str]
    prefix_to_dir: dict[str, dict[str, object]]
    model_presets: list[dict[str, object]]


def _split_origins(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def get_settings() -> Settings:
    backend_root = Path(__file__).resolve().parents[3]
    admin_root = backend_root.parent
    repo_root = admin_root.parent
    blog_root = repo_root / "blog-content"
    prefix_to_dir: dict[str, dict[str, object]] = {
        "ts": {"dir": "tech-study", "category": "技术研习", "cover": "/img/covers/tech-study.svg"},
        "pr": {"dir": "pitfall-review", "category": "踩坑复盘", "cover": "/img/covers/pitfall-review.svg"},
        "pp": {"dir": "project-practice", "category": "项目实战", "cover": "/img/covers/project-practice.svg"},
        "ge": {"dir": "growth-essay", "category": "成长随笔", "cover": "/img/covers/growth-essay.svg"},
        "rs": {"dir": "resource-sharing", "category": "资源分享", "cover": "/img/covers/resource-sharing.svg"},
    }
    model_presets: list[dict[str, object]] = [
        {
            "id": "deepseek",
            "name": "DeepSeek V4 Pro",
            "baseUrl": "https://api.deepseek.com",
            "modelId": "deepseek-v4-pro",
            "provider": "deepseek",
            "apiFormat": "openai",
            "anthropicBaseUrl": "https://api.deepseek.com/anthropic",
            "thinkingMode": "enabled",
            "reasoningEffort": "max",
            "agentMode": True,
            "toolCalls": True,
            "strictToolCalls": False,
            "jsonMode": True,
            "temperature": 0.3,
            "maxTokens": 8192,
        },
        {
            "id": "deepseek-flash",
            "name": "DeepSeek V4 Flash",
            "baseUrl": "https://api.deepseek.com",
            "modelId": "deepseek-v4-flash",
            "provider": "deepseek",
            "apiFormat": "openai",
            "anthropicBaseUrl": "https://api.deepseek.com/anthropic",
            "thinkingMode": "enabled",
            "reasoningEffort": "high",
            "agentMode": True,
            "toolCalls": True,
            "strictToolCalls": False,
            "jsonMode": True,
            "temperature": 0.3,
            "maxTokens": 8192,
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
    return Settings(
        repo_root=repo_root,
        admin_root=admin_root,
        backend_root=backend_root,
        blog_root=blog_root,
        posts_dir=blog_root / "source" / "_posts",
        category_registry_path=blog_root / "config" / "category-registry.json",
        cache_dir=admin_root / ".cache",
        server_host=os.getenv("BLOG_ADMIN_HOST", "0.0.0.0"),
        server_port=int(os.getenv("BLOG_ADMIN_PORT", "15000")),
        cors_origins=_split_origins(
            os.getenv(
                "BLOG_ADMIN_CORS_ORIGINS",
                "http://localhost:4000,http://localhost:14000,http://localhost:3000",
            )
        ),
        prefix_to_dir=prefix_to_dir,
        model_presets=model_presets,
    )


settings = get_settings()
