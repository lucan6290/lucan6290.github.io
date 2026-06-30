"""领域模型定义。

存放与业务概念对应的枚举、值对象等，区别于 schemas/ 下的对外传输 DTO。
"""

from enum import Enum


class ArticleType(str, Enum):
    """文章类型枚举。

    继承 str 使其成员可直接序列化为 JSON 字符串，
    并在 API 查询参数中以字符串字面量（docs / blog）参与校验。
    """

    docs = "docs"  # 文档类文章，对应 site/docs 目录
    blog = "blog"  # 博客类文章，对应 site/blog 目录
