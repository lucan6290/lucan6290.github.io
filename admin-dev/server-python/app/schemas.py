"""
博客管理后台 - Pydantic 数据模型
对齐 Node.js 后端的 API 契约，前端无需修改
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# ============================================================
# 通用响应
# ============================================================

class ApiResponse(BaseModel):
    """统一 API 响应格式"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


# ============================================================
# 文章状态
# ============================================================

class PostStatus(str, Enum):
    DRAFT = "draft"
    WIP = "wip"
    PUBLISHED = "published"


# ============================================================
# Front Matter
# ============================================================

class FrontMatter(BaseModel):
    """文章 Front Matter 结构"""
    title: str = ""
    date: str = ""
    updated: Optional[str] = None
    categories: Optional[List[Any]] = None  # ["一级", "二级"] 或 [["一级", "二级"]]
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    layout: Optional[str] = None
    comments: Optional[bool] = None
    permalink: Optional[str] = None
    excerpt: Optional[str] = None
    published: Optional[bool] = None
    lang: Optional[str] = None
    cover: Optional[str] = None
    sticky: Optional[int] = None
    slug: Optional[str] = None
    status: Optional[PostStatus] = None
    series: Optional[str] = None
    series_order: Optional[int] = None


# ============================================================
# 文章信息（列表 / 详情）
# ============================================================

class PostInfo(BaseModel):
    """文章基本信息"""
    title: str = ""
    path: str = ""
    date: str = ""
    updated: Optional[str] = None
    categories: List[str] = []
    tags: List[str] = []
    description: Optional[str] = None
    cover: Optional[str] = None
    status: PostStatus = PostStatus.PUBLISHED
    series: Optional[str] = None
    seriesOrder: Optional[int] = None


class PostDetail(BaseModel):
    """文章详情（含内容和 Front Matter）"""
    frontMatter: Optional[Dict[str, Any]] = None
    content: Optional[str] = None   # 正文（不含 Front Matter）
    raw: Optional[str] = None       # 原始完整内容


# ============================================================
# 请求模型
# ============================================================

class CreatePostRequest(BaseModel):
    """创建文章请求 - 只需三个参数，hexo np 自动处理模板/分类/封面等"""
    title: str                                    # 文章标题
    prefix1: str                                  # 一级前缀: ts/pr/pp/ge/rs
    prefix2: str                                  # 二级前缀: vue3/docker/blog 等


class UpdatePostRequest(BaseModel):
    """更新文章请求"""
    frontMatter: Optional[Dict[str, Any]] = None
    content: Optional[str] = None


class UploadImageRequest(BaseModel):
    """上传图片请求"""
    articlePath: str
    imageData: str   # Base64 编码
    extension: str   # png / jpg / gif / svg


class GitCommitRequest(BaseModel):
    """Git 提交请求"""
    message: str


# ============================================================
# 图片信息
# ============================================================

class ImageInfo(BaseModel):
    """图片信息"""
    name: str
    path: str
    url: str


# ============================================================
# AI 相关
# ============================================================

class ChatMessage(BaseModel):
    """对话消息"""
    role: str      # system / user / assistant
    content: str


class ChatRequest(BaseModel):
    """AI 对话请求"""
    messages: List[ChatMessage]
    baseUrl: str = ""
    apiKey: str = ""
    modelId: str = ""
    stream: bool = True
    temperature: float = 0.7
    maxTokens: int = 4096


class TestConnectionRequest(BaseModel):
    """AI 连接测试请求"""
    baseUrl: str
    apiKey: str
    modelId: str


class ModelPreset(BaseModel):
    """模型预设"""
    id: str
    name: str
    baseUrl: str
    modelId: str
