"""管理员登录接口。"""

from http import HTTPStatus

from fastapi import APIRouter, Request

from scr.core.auth import authenticate_admin, create_access_token
from scr.core.exceptions import AppError
from scr.schemas.auth import LoginRequestDTO, LoginResponseDTO, SessionResponseDTO


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponseDTO)
def login(payload: LoginRequestDTO) -> LoginResponseDTO:
    """校验单管理员账号密码并签发 token。"""
    if not authenticate_admin(payload.username, payload.password):
        raise AppError(
            "账号或密码不正确。",
            code="invalid_credentials",
            status_code=HTTPStatus.UNAUTHORIZED,
        )

    token, expires_at = create_access_token(payload.username)
    return LoginResponseDTO(
        access_token=token,
        expires_at=expires_at,
        username=payload.username,
    )


@router.get("/me", response_model=SessionResponseDTO)
def current_session(request: Request) -> SessionResponseDTO:
    """返回当前 token 对应的会话信息。"""
    return SessionResponseDTO(
        authenticated=True,
        username=request.state.auth_user,
        expires_at=request.state.auth_expires_at,
    )
