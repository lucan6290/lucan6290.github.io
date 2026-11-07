"""AI 写作 HTTP 适配，使用桌面内容服务的会话认证。"""
from pathlib import Path
from typing import Literal

from fastapi import APIRouter
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from ai_writing import AiSettingsStore, complete
from content_store import ContentError


class PrivateRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def private_handler(request):
            try:
                response = await handler(request)
            except RequestValidationError:
                # Pydantic 验证错误会带有原始输入，不能回显密钥、指令或正文。
                response = JSONResponse(status_code=400, content={"code": "invalid_request", "message": "AI 请求字段无效"})
            response.headers["Cache-Control"] = "no-store"
            return response

        return private_handler


class AiPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class SettingsPayload(AiPayload):
    base_url: str = Field(min_length=1, max_length=2048)
    model: str = Field(min_length=1, max_length=200)
    api_key: SecretStr | None = None
    key_mode: Literal["session", "windows", "clear"] | None = None


class ComposePayload(AiPayload):
    operation: Literal["generate", "rewrite"]
    instruction: str = Field(min_length=1, max_length=4000)
    body: str | None = Field(default=None, max_length=60000)


def create_ai_router(state_dir: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/ai", route_class=PrivateRoute)
    store = AiSettingsStore(state_dir)

    @router.get("/settings")
    def settings():
        return store.public_settings()

    @router.put("/settings")
    def save_settings(payload: SettingsPayload):
        key = payload.api_key.get_secret_value() if payload.api_key is not None else None
        return store.save(payload.base_url, payload.model, key, payload.key_mode)

    @router.post("/test")
    async def test_connection():
        await complete(store.provider(), [{"role": "user", "content": "Reply with just OK."}], max_tokens=32)
        return {"ok": True}

    @router.post("/compose")
    async def compose(payload: ComposePayload):
        instruction = payload.instruction.strip()
        if not instruction:
            raise ContentError(400, "ai_empty_instruction", "请输入写作要求。")
        system = ("你是技术写作助手。只输出 Markdown 正文，不添加 YAML Front Matter，"
                  "不把全文包裹在代码围栏里，不输出开场白。")
        user = f"写作要求：\n{instruction}"
        if payload.operation == "rewrite":
            if payload.body is None or not payload.body.strip():
                raise ContentError(400, "ai_empty_body", "请先写入要改写的正文。")
            system += "根据要求改写现有正文，保留首个一级标题，除非写作要求明确要求修改。"
            user += f"\n\n待改写的 Markdown 正文：\n{payload.body}"
        elif payload.body is not None:
            raise ContentError(400, "ai_unexpected_body", "生成请求只需填写写作要求。")
        markdown = await complete(store.provider(), [{"role": "system", "content": system}, {"role": "user", "content": user}])
        return {"markdown": markdown}

    return router