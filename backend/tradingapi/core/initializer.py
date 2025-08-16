from contextlib import asynccontextmanager

from loguru import logger

import tradingapi.fetcher.datasources
from tradingapi.fetcher.manager import manager

from .config import app_config
from .db import db_manager
from .logging import setup_logging


@asynccontextmanager
async def lifespan(app):
    """应用生命周期管理"""
    # 初始化系统组件
    setup_logging()
    manager.complete_registration()
    await db_manager.initialize()
    logger.success("Application initialized")

    yield  # 应用运行期间

    # 关闭资源
    await db_manager.close()
    logger.success("Application shutdown")
