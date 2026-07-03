"""应用配置管理。

通过环境变量与项目目录约定，组装不可变的 Settings 实例，
供日志、文件系统、服务层等模块统一读取。
"""

import os
from dataclasses import dataclass
from pathlib import Path


def _backend_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_dotenv() -> None:
    """加载 admin/backend/.env，已存在的系统环境变量优先级更高。"""
    env_path = _backend_dir() / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _default_project_root() -> Path:
    # 当前文件位于 <project_root>/admin/backend/scr/core/config.py，向上回溯 4 层即为项目根
    return Path(__file__).resolve().parents[4]


def _default_cors_origins() -> list[str]:
    # 本地开发固定只允许管理前端端口；临时来源请使用 LUCHUAN_CORS_ORIGINS 覆盖。
    # 同时列出 localhost 与 127.0.0.1 两种写法，浏览器对二者视为不同源
    return [
        "http://localhost:14000",
        "http://127.0.0.1:14000",
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
    blog_sidebars_path: Path  # 博客侧边栏配置文件（site/blogSidebars.ts）
    docusaurus_config_path: Path  # Docusaurus 配置文件（site/docusaurus.config.ts）
    content_schema_dir: Path  # 内容校验 schema 目录（admin/backend/data/content-schema）
    registry_index_path: Path  # 管理后台 SQLite 索引库路径
    cors_origins: list[str]  # 允许跨域的前端来源列表
    admin_username: str  # 管理员登录账号
    admin_password: str  # 管理员登录密码，本地默认值仅用于开发
    auth_secret: str  # token 签名密钥
    auth_token_ttl_minutes: int  # 登录 token 有效期，单位分钟


def load_settings() -> Settings:
    """根据环境变量与目录约定构造 Settings。"""
    _load_dotenv()

    # 支持通过环境变量覆盖默认项目根，默认回溯到源码目录之上 4 层
    project_root = Path(os.getenv("LUCHUAN_PROJECT_ROOT", _default_project_root())).resolve()
    site_dir = project_root / "site"

    admin_username = os.getenv("LUCHUAN_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("LUCHUAN_ADMIN_PASSWORD", "admin123")

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
        blog_sidebars_path=site_dir / "blogSidebars.ts",
        docusaurus_config_path=site_dir / "docusaurus.config.ts",
        content_schema_dir=project_root / "admin" / "backend" / "data" / "content-schema",
        registry_index_path=Path(
            os.getenv("LUCHUAN_REGISTRY_INDEX_PATH", project_root / "admin" / "backend" / "data" / "registry_index.sqlite3")
        ).resolve(),
        cors_origins=_load_cors_origins(),
        admin_username=admin_username,
        admin_password=admin_password,
        auth_secret=os.getenv("LUCHUAN_AUTH_SECRET", admin_password),
        auth_token_ttl_minutes=int(os.getenv("LUCHUAN_AUTH_TOKEN_TTL_MINUTES", "720")),
    )


# 模块级全局单例，进程启动时加载一次，供各模块直接 import 使用
settings = load_settings()
