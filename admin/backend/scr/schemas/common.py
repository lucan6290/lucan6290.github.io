"""通用响应数据传输对象（DTO）。

定义与具体业务资源无关的响应结构，如错误响应与健康检查响应。
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponseDTO(BaseModel):
    """统一错误响应结构，与全局异常处理器输出对齐。"""

    code: str  # 业务错误代码，如 not_found / bad_request
    message: str  # 面向用户的错误提示
    request_id: str | None = None  # 请求追踪 ID，便于关联日志
    details: dict[str, object] = Field(default_factory=dict)  # 补充细节，如字段级校验错误


class HealthResponseDTO(BaseModel):
    """健康检查响应，供探活与版本核对使用。"""

    status: str  # 服务状态，正常返回 ok
    version: str  # 当前应用版本号
    environment: str  # 运行环境标识


class FileChangeDTO(BaseModel):
    """危险操作预演中的单个文件变更项。"""

    model_config = ConfigDict(populate_by_name=True)

    action: Literal["create", "update", "delete", "move", "replace"]
    target: str
    from_: str | None = Field(default=None, alias="from")
    to: str | None = None
    description: str


class MutationPlanDTO(BaseModel):
    """危险操作预演或执行后的变更计划。"""

    dry_run: bool
    requires_confirmation: bool
    changes: list[FileChangeDTO] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
