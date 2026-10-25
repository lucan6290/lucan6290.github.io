"""Shared OpenAPI response declarations for v1 endpoints."""

from typing import Any

from scr.schemas.common import ErrorResponseDTO


COMMON_ERROR_RESPONSES: dict[int, dict[str, Any]] = {
    400: {
        "model": ErrorResponseDTO,
        "description": "Bad request.",
    },
    401: {
        "model": ErrorResponseDTO,
        "description": "Authentication is required or invalid.",
    },
    404: {
        "model": ErrorResponseDTO,
        "description": "Resource not found.",
    },
    409: {
        "model": ErrorResponseDTO,
        "description": "Resource conflict.",
    },
    422: {
        "model": ErrorResponseDTO,
        "description": "Request validation failed.",
    },
    428: {
        "model": ErrorResponseDTO,
        "description": "A required precondition is missing.",
    },
    500: {
        "model": ErrorResponseDTO,
        "description": "Unexpected server error.",
    },
}
