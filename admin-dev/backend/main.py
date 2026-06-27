"""博客管理后台 - 破坏式重构后的入口。"""
from __future__ import annotations

import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from blog_admin.core.settings import settings  # noqa: E402

if __name__ == "__main__":
    print("博客管理后台服务器 (Python FastAPI) 启动中...")
    print(f"  地址: http://localhost:{settings.server_port}")
    print(f"  API 文档: http://localhost:{settings.server_port}/docs")
    print(f"  健康检查: http://localhost:{settings.server_port}/api/admin/v1/health")
    uvicorn.run(
        "blog_admin.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True,
        reload_dirs=["src"],
    )
