"""桌面端后端 Sidecar 入口。

在 Tauri 桌面端模式下启动 FastAPI 应用：
- 接受 CLI 参数 --port / --project-root
- 动态添加 admin/backend 到 sys.path，复用原后端代码
- 禁用 --reload（桌面模式不需要文件监听）
- 放宽 CORS 以适配 Tauri WebView 源

使用方式（开发模式）：
    python admin-desktop/src-backend/main.py --port 18001 --project-root /path/to/xiaocancoding
"""

import argparse
import os
import sys
from pathlib import Path


def resolve_backend_source_dir() -> Path:
    """定位 admin/backend/ 源码目录。

    优先从本文件位置向上查找 admin/backend/，
    回退到从 cwd 向上查找。
    """
    # 本文件位于 admin-desktop/src-backend/main.py
    # admin/backend/ 在同级目录的上两层
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent.parent / "admin" / "backend",  # 项目根下的 admin/backend
    ]
    for c in candidates:
        if c.exists() and (c / "scr" / "main.py").exists():
            return c

    # 从 cwd 向上查找
    cwd = Path.cwd()
    for _ in range(6):
        backend_dir = cwd / "admin" / "backend"
        if backend_dir.exists() and (backend_dir / "scr" / "main.py").exists():
            return backend_dir
        cwd = cwd.parent

    raise RuntimeError("无法定位 admin/backend/ 源码目录")


def main():
    parser = argparse.ArgumentParser(description="箓川码笺桌面端后端 Sidecar")
    parser.add_argument("--port", type=int, default=18000, help="监听端口")
    parser.add_argument("--project-root", type=str, default=None, help="项目根目录")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="监听地址")
    args = parser.parse_args()

    # 设置环境变量（在 import scr 之前生效）
    if args.project_root:
        os.environ["LUCHUAN_PROJECT_ROOT"] = args.project_root

    # CORS：允许 Tauri WebView 源 + 开发模式 Vite 源
    tauri_origins = [
        "http://tauri.localhost",      # Windows WebView2
        "https://tauri.localhost",     # Windows WebView2 (https)
        "tauri://localhost",           # macOS WKWebView
        "http://localhost:14200",      # 开发模式 Vite
        "http://127.0.0.1:14200",      # 开发模式 Vite
    ]
    existing = os.environ.get("LUCHUAN_CORS_ORIGINS", "")
    if existing:
        tauri_origins = existing.split(",") + tauri_origins
    os.environ["LUCHUAN_CORS_ORIGINS"] = ",".join(tauri_origins)

    # 添加后端源码到 sys.path
    backend_dir = resolve_backend_source_dir()
    backend_str = str(backend_dir)
    if backend_str not in sys.path:
        sys.path.insert(0, backend_str)

    # 切换工作目录到 backend_dir，使相对路径（如 .env、data/）可用
    os.chdir(backend_dir)

    # 延迟导入，确保环境变量和 sys.path 已就绪
    import uvicorn
    from scr.main import app  # noqa: E402

    print(f"[desktop-sidecar] Backend source: {backend_dir}")
    print(f"[desktop-sidecar] Project root: {args.project_root or '(default)'}")
    print(f"[desktop-sidecar] Listening on {args.host}:{args.port}")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=False,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    main()
