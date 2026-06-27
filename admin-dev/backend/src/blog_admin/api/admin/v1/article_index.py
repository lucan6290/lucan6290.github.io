from __future__ import annotations

from fastapi import APIRouter

from blog_admin.modules.article_index import application
from blog_admin.modules.article_index.schemas import ArticleIndexScanRequest, KnowledgeQARequest

router = APIRouter(prefix="/articles", tags=["文章索引"])


@router.post("/index/scan")
async def scan_article_index(req: ArticleIndexScanRequest):
    return await application.scan_article_index(req)


@router.get("/index")
async def get_article_index(includeDrafts: bool = True, autoRefresh: bool = True):
    return await application.get_article_index(include_drafts=includeDrafts, auto_refresh=autoRefresh)


@router.post("/knowledge-qa")
async def knowledge_qa(req: KnowledgeQARequest):
    return await application.knowledge_qa(req)
