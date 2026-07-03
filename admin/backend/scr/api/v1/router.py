"""API v1 路由聚合。

将各业务端点子路由统一挂载到 /v1 前缀下，
由 main.py 以 /api 前缀整体引入，最终路径形如 /api/v1/...。
"""

from fastapi import APIRouter

from scr.api.v1.responses import COMMON_ERROR_RESPONSES
from scr.api.v1.endpoints import (
    articles,
    auth,
    build,
    categories,
    docusaurus_config,
    health,
    registry_index,
    schema,
    sidebars,
    tags,
    validation,
)


api_router = APIRouter(prefix="/v1", responses=COMMON_ERROR_RESPONSES)
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(articles.router)
api_router.include_router(categories.router)
api_router.include_router(tags.router)
api_router.include_router(sidebars.router)
api_router.include_router(schema.router)
api_router.include_router(registry_index.router)
api_router.include_router(validation.router)
api_router.include_router(build.router)
api_router.include_router(docusaurus_config.router)
