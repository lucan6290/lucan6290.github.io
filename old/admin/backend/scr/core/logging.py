"""日志配置。

使用 logging.config.dictConfig 以字典方式统一配置根日志器，
输出格式为：时间 级别 [日志器名] 消息。
"""

import logging.config

from scr.core.config import settings


def configure_logging() -> None:
    """根据 settings.log_level 配置控制台日志。"""
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,  # 保留第三方库已有的日志器
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                }
            },
            "root": {
                "handlers": ["console"],
                "level": settings.log_level,
            },
        }
    )
