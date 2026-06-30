"""应用配置管理。

通过环境变量与项目目录约定，组装不可变的 Settings 实例，
供日志、文件系统、服务层等模块统一读取。
"""

import os
from dataclasses import dataclass
from pathlib import Path


def _default_project_root() -> Path:
    # 当前文件位于 <project_root>/admin/backend/scr/core/config.py，向上回溯 4 层即为项目根
    return Path(__file__).resolve().parents[4]


def _default_cors_origins() -> list[str]:
    # 本地开发常见前端端口：admin 前端 Vite 默认 14000、通用 Vite 5173、Next.js 3000
    # 同时列出 localhost 与 127.0.0.1 两种写法，浏览器对二者视为不同源
    return [
        "http://localhost:14000",
        "http://127.0.0.1:14000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def _load_cors_origins() -> list[str]:
    # 支持通过 LUCHUAN_CORS_ORIGINS 环境变量（逗号分隔）覆盖默认白名单；缺省走内置端口表
    raw = os.getenv("LUCHUAN_CORS_ORIGINS", "")
    if not raw.strip():
        return _default_cors_origins()
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    """全局配置项，frozen=True 保证运行期不可变。"""

    app_name: str  # 应用名称
    app_version: str  # 应用版本号，同时用于 /health 与 OpenAPI 文档
    environment: str  # 运行环境标识，如 local / prod
    log_level: str  # 日志级别（DEBUG / INFO / WARNING ...）
    project_root: Path  # 项目根目录绝对路径
    site_dir: Path  # Docusaurus 站点目录（project_root/site）
    docs_dir: Path  # docs 文章根目录（site/docs）
    blog_dir: Path  # blog 文章根目录（site/blog）
    sidebars_path: Path  # 侧边栏配置文件（site/sidebars.ts）
    docusaurus_config_path: Path  # Docusaurus 配置文件（site/docusaurus.config.ts）
    content_schema_dir: Path  # 内容校验 schema 目录（admin/backend/data/content-schema）
    registry_index_path: Path  # 管理后台 SQLite 索引库路径
    cors_origins: list[str]  # 允许跨域的前端来源列表


def load_settings() -> Settings:
    """根据环境变量与目录约定构造 Settings。"""
    # 支持通过环境变量覆盖默认项目根，默认回溯到源码目录之上 4 层
    project_root = Path(os.getenv("LUCHUAN_PROJECT_ROOT", _default_project_root())).resolve()
    site_dir = project_root / "site"

    return Settings(
        app_name="箓川码笺 Admin Backend",
        app_version="0.1.0",
        # 环境与日志级别均允许通过环境变量注入，缺省值适配本地开发
        environment=os.getenv("LUCHUAN_ENV", "local"),
        log_level=os.getenv("LUCHUAN_LOG_LEVEL", "INFO"),
        project_root=project_root,
        site_dir=site_dir,
        docs_dir=site_dir / "docs",
        blog_dir=site_dir / "blog",
        sidebars_path=site_dir / "sidebars.ts",
        docusaurus_config_path=site_dir / "docusaurus.config.ts",
        content_schema_dir=project_root / "admin" / "backend" / "data" / "content-schema",
        registry_index_path=Path(
            os.getenv("LUCHUAN_REGISTRY_INDEX_PATH", project_root / "admin" / "backend" / "data" / "registry_index.sqlite3")
        ).resolve(),
        cors_origins=_load_cors_origins(),
    )


# 模块级全局单例，进程启动时加载一次，供各模块直接 import 使用
settings = load_settings()
