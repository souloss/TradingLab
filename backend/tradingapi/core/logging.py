import os
import sys

from loguru import logger

from .config import app_config


def setup_logging():
    """配置Loguru日志系统"""
    logger.remove()  # 移除默认handler

    # 判断是否为开发环境
    is_development = (
        os.getenv("ENVIRONMENT") == "development"
        or os.getenv("DEBUG") == "1"
        or not os.getenv("ENVIRONMENT")
        or app_config.ENV == "dev"
    )

    # 根据环境选择不同的日志格式
    if is_development:
        # 开发环境：使用VSCode可识别的格式，包含完整文件路径
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{file.path}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    else:
        # 生产环境：使用简洁格式，只显示相对路径
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{file.name}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

    # 配置控制台输出
    logger.add(
        sys.stderr,
        level=app_config.LOG_LEVEL,
        format=console_format,
        enqueue=True,  # 支持异步安全
    )

    # 配置文件输出
    if app_config.LOG_DIR:
        logger.add(
            f"{app_config.LOG_DIR}/tradingapi_{{time:YYYY-MM-DD}}.log",
            rotation="00:00",  # 每天轮转
            retention="30 days",  # 保留30天
            level=app_config.LOG_LEVEL,
            encoding="utf-8",
            format=console_format,
        )

    logger.info(f"Logging initialized with level: {app_config.LOG_LEVEL}")
