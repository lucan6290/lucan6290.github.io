# api/v1/endpoints — AGENTS.md

> 业务端点层（Controller）。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md` 第 4/16/17 节。

## 职责

每个业务域一个文件，只做参数绑定、路由与薄编排，不承载业务逻辑。

## 内容

agents / ai_models / articles / auth / build / categories / deploy / docusaurus_config / git_sync / health / registry_index / schema / sidebars / sync / tags / validation。

## 约定

- `router = APIRouter(prefix="/<resource>", tags=["<resource>"])`。
- 服务经 `Depends` 注入，不直接 new Service。
- 业务逻辑下沉到 application/services。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
