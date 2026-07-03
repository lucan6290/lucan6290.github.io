"""管理员登录与会话 DTO。"""

from pydantic import BaseModel, Field


class LoginRequestDTO(BaseModel):
    """登录请求。"""

    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class LoginResponseDTO(BaseModel):
    """登录成功后的 token 响应。"""

    access_token: str
    token_type: str = "bearer"
    expires_at: int
    username: str


class SessionResponseDTO(BaseModel):
    """当前登录会话。"""

    authenticated: bool
    username: str
    expires_at: int
