"""FastAPI 应用入口。

负责按顺序组装应用：配置日志 → 创建 app → 注册中间件与 CORS →
注册异常处理器 → 挂载 API 路由。由 uvicorn 加载本模块的 app 对象启动服务。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from scr.api.v1.router import api_router
from scr.core.config import settings
from scr.core.exception_handlers import register_exception_handlers
from scr.core.logging import configure_logging
from scr.core.middleware import request_context_middleware


# 进程启动时先完成日志配置，保证后续启动流程可被记录
configure_logging()

app = FastAPI(
    title=settings.app_name,
    description="Local-first content management API for the Docusaurus site.",
    version=settings.app_version,
)

# 请求上下文中间件：注入 request_id 并记录请求耗时
app.middleware("http")(request_context_middleware)

# 跨域配置：允许前端开发端口（3000 / 5173）携带凭证访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)  # 统一异常响应格式
app.include_router(api_router, prefix="/api")  # 所有业务路由统一前缀 /api


if __name__ == "__main__":
    # 直接运行入口：在 admin/backend/ 目录下执行 `python -m scr.main` 启动开发服务。
    # 必须用 `-m` 模块方式启动，不能直接 `python scr/main.py`，否则 `scr` 包无法被解析。
    import uvicorn

    uvicorn.run("scr.main:app", host="127.0.0.1", port=18000, reload=True)
