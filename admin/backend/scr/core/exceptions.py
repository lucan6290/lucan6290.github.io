"""应用自定义异常体系。

所有业务异常均继承 AppError，由全局异常处理器（exception_handlers）统一捕获，
转换为带有 code / message / request_id / details 的 JSON 响应。
"""

from http import HTTPStatus
from typing import Any


class AppError(Exception):
    """应用异常基类。

    子类通过类属性覆盖默认的 status_code / code / message；
    实例化时也可临时传入 message / code / status_code / details 定制单次错误。
    """

    status_code = HTTPStatus.INTERNAL_SERVER_ERROR  # 默认 HTTP 状态码
    code = "internal_error"  # 默认业务错误代码
    message = "服务暂时不可用。"  # 默认面向用户的提示文案

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        status_code: int | HTTPStatus | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        # 未显式传参时回退到类属性默认值，实现"可选覆盖"
        self.message = message or self.message
        self.code = code or self.code
        self.status_code = int(status_code or self.status_code)
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppError):
    """资源不存在（404）。"""

    status_code = HTTPStatus.NOT_FOUND
    code = "not_found"
    message = "资源不存在。"


class BadRequestError(AppError):
    """请求参数不合法（400）。"""

    status_code = HTTPStatus.BAD_REQUEST
    code = "bad_request"
    message = "请求参数不合法。"


class ConflictError(AppError):
    """资源冲突（409）。"""

    status_code = HTTPStatus.CONFLICT
    code = "conflict"
    message = "资源已存在。"


class PreconditionRequiredError(AppError):
    """请求缺少必要前置条件（428）。"""

    status_code = HTTPStatus.PRECONDITION_REQUIRED
    code = "precondition_required"
    message = "缺少必要前置条件。"
