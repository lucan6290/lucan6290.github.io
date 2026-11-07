"""独立桌面内容后端入口，固定本地端口，支持开发热更新。"""
import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import tempfile

import uvicorn
from uvicorn.supervisors import ChangeReload

from app import create_app


def resolve_project_root(explicit: Path | None = None, *, development=True):
    candidates = [explicit] if explicit is not None else [Path.cwd(), *Path.cwd().parents]
    for candidate in candidates:
        root = candidate.resolve()
        content = (root / "frontend/content").resolve()
        if content.is_dir() and content.is_relative_to(root) and (not development or (root / "admin-desktop").is_dir()):
            return root
    raise RuntimeError("无法定位博客目录：需要 frontend/content" + (" 与 admin-desktop" if development else ""))


def prepare_session(project_root: Path, session_file: Path):
    session = {"token": secrets.token_urlsafe(32), "project_root": str(project_root.resolve()),
               "content_root": str((project_root / "frontend/content").resolve())}
    session_file.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=session_file.parent,
                                         prefix=".session-", delete=False) as output:
            temporary = Path(output.name)
            json.dump(session, output, ensure_ascii=False)
        os.replace(temporary, session_file)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return session


def create_runtime_app():
    # reload 子进程继承同一 token，文件变化不会使桌面会话失效。
    state = os.environ.get("XIAOCAN_DESKTOP_STATE_DIR")
    return create_app(Path(os.environ["XIAOCAN_DESKTOP_PROJECT_ROOT"]), os.environ["XIAOCAN_DESKTOP_TOKEN"],
                      Path(state) if state else None)


def main():
    parser = argparse.ArgumentParser(description="箓川码笺独立桌面内容后端")
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--port", type=int, choices=[18000], default=18000)
    parser.add_argument("--reload", action="store_true", help="开发模式热更新")
    parser.add_argument("--session-file", type=Path)
    args = parser.parse_args()
    try:
        root = resolve_project_root(args.project_root, development=args.reload or args.project_root is None)
        entry = "main:create_runtime_app" if args.reload else create_runtime_app
        config = uvicorn.Config(entry, factory=True, host="127.0.0.1", port=args.port,
                                reload=args.reload, reload_dirs=[str(Path(__file__).resolve().parent)] if args.reload else None,
                                loop="asyncio", http="h11", ws="none", lifespan="on",
                                access_log=False)
        # 先持有监听 socket，再发布会话。Windows 排他绑定避免 SO_REUSEADDR 重绑；
        # socket 一直传给 Uvicorn/reloader，不能检查端口后关闭再重新绑定。
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            if os.name == "nt":
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            else:
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind((config.host, config.port))
            listener.listen(config.backlog)
            listener.set_inheritable(True)
            session_file = args.session_file or root / ".codex-tmp/admin-desktop/session.json"
            session_file = session_file.resolve()
            if session_file.is_relative_to((root / "frontend/content").resolve()):
                raise RuntimeError("会话文件不得位于博客内容目录内")
            session = prepare_session(root, session_file)
            os.environ["XIAOCAN_DESKTOP_STATE_DIR"] = str(session_file.parent)
            os.environ["XIAOCAN_DESKTOP_PROJECT_ROOT"] = session["project_root"]
            os.environ["XIAOCAN_DESKTOP_TOKEN"] = session["token"]
            server = uvicorn.Server(config)
            if config.should_reload:
                ChangeReload(config, target=server.run, sockets=[listener]).run()
            else:
                server.run(sockets=[listener])
                if not server.started:
                    raise RuntimeError("内容服务未能完成启动")
    except (RuntimeError, OSError) as error:
        parser.exit(1, f"内容后端启动失败：{error}\n")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
