# core — AGENTS.md

> 跨切面能力层。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md`。

## 职责

提供被各层复用的横切能力，不承载具体业务。

## 内容

- `config.py`：Settings 配置（frozen dataclass + 环境变量）
- `auth.py`：HMAC token 签发/校验 + 鉴权中间件
- `exceptions.py`：AppError 异常层级
- `exception_handlers.py`：统一异常响应
- `middleware.py`：request_id 注入 + 请求耗时日志
- `logging.py`：dictConfig 日志配置
- `security.py`：路径安全等安全边界

## 约定

- 横切能力，不 import services/application。
- 详见 BACKEND_CONVENTION 第 8/9/16/19 节。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
