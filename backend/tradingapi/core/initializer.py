from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from tradingapi.fetcher.manager import manager
from tradingapi.tasks.base import init_scheduler_tasks
from tradingapi.tasks.scheduler import TaskScheduler

from .config import app_config
from .db import db_manager
from .logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 初始化系统组件
    setup_logging()
    manager.complete_registration()
    await db_manager.initialize()
    task_scheduler = TaskScheduler(
        url=app_config.SQLITE_SYNC_DRIVER + ":///" + app_config.SQLITE_DB_PATH,
        use_async=True,
    )
    init_scheduler_tasks(task_scheduler)
    task_scheduler.start()
    logger.success("Application initialized")

    try:
        yield  # 应用运行期间
    finally:
        # 关闭资源
        task_scheduler.shutdown()
        await db_manager.close()
        logger.success("Application shutdown")
