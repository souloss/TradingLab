# app/core/db.py
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

import tradingapi.models

from .config import app_config


class DatabaseManager:
    """数据库管理器 - 单例模式"""

    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self) -> None:
        """初始化数据库连接"""
        if self._engine is not None:
            return

        # 确保 SQLite 文件存在
        if (
            "sqlite" in app_config.DATABASE_URL
            and app_config.SQLITE_DB_PATH != ":memory:"
        ):
            db_path = Path(app_config.SQLITE_DB_PATH)
            if not db_path.exists():
                db_path.parent.mkdir(parents=True, exist_ok=True)
                db_path.touch()
                logger.info(f"Created SQLite database at {db_path}")

        # 连接参数
        connect_args = {}
        if app_config.SQLITE_ASYNC_DRIVER.endswith("aiosqlite"):
            connect_args = {"check_same_thread": False}

        # 创建引擎
        self._engine = create_async_engine(
            app_config.DATABASE_URL,
            echo=app_config.DEBUG,
            future=True,
            poolclass=NullPool if "sqlite" in app_config.DATABASE_URL else None,
            connect_args=connect_args,
        )

        # 创建会话工厂
        self._session_factory = async_sessionmaker(
            bind=self._engine, class_=AsyncSession, expire_on_commit=False
        )

        # 创建表
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("Database tables created")

        logger.info(f"Database initialized: {app_config.DATABASE_URL}")

    async def close(self) -> None:
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database engine disposed")

    def get_session_factory(self):
        """获取会话工厂"""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized")
        return self._session_factory


# 全局数据库管理器实例
db_manager = DatabaseManager()


# 依赖注入函数
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖注入函数"""
    session_factory = db_manager.get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
