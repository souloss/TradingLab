from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

import tradingapi.fetcher.datasources
from tradingapi.fetcher.manager import manager
from tradingapi.tasks.base import init_scheduler_tasks
from .config import app_config
from .db import db_manager, get_session_with_ctx
from .logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 初始化系统组件
    setup_logging()
    manager.complete_registration()
    await db_manager.initialize()

    async with get_session_with_ctx() as session:
        task_scheduler = init_scheduler_tasks(session=session)
        task_scheduler.start()
    logger.success("Application initialized")

    try:
        yield  # 应用运行期间
    finally:
        # 关闭资源
        task_scheduler.shutdown()
        await db_manager.close()
        logger.success("Application shutdown")
