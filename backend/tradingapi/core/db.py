import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text
from sqlmodel import SQLModel

from .config import app_config


class DatabaseManager:
    """异步数据库管理器（支持 SQLite + PostgreSQL）"""

    _instance: Optional["DatabaseManager"] = None
    _engine = None
    _session_factory = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = False

    async def initialize(self):
        """初始化异步数据库引擎"""

        if self.initialized:
            return

        async with self._lock:
            if self.initialized:
                return

            logger.info(f"Initializing database: {app_config.DATABASE_URL}")

            url = app_config.DATABASE_URL

            engine_kwargs = dict(
                echo=app_config.DEBUG,
                future=True,
            )

            # -------------------------------
            # SQLite 配置
            # -------------------------------
            if url.startswith("sqlite"):
                engine_kwargs.update(
                    {
                        "connect_args": {
                            "check_same_thread": False,
                        },
                    }
                )

            # -------------------------------
            # PostgreSQL（asyncpg）配置
            # -------------------------------
            elif url.startswith("postgresql+asyncpg"):
                engine_kwargs.update(
                    {
                        "pool_size": 10,
                        "max_overflow": 20,
                        "pool_recycle": 3600,
                        "pool_pre_ping": True,
                    }
                )

            else:
                raise RuntimeError(f"Unsupported DB URL: {url}")

            # ✔ 创建异步引擎（正确使用 async Pool）
            self._engine = create_async_engine(url, **engine_kwargs)

            # 会话管理器
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                autoflush=False,
                expire_on_commit=False,
            )

            # 创建表
            async with self._engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)

                # ✔ 异步设置 SQLite PRAGMA （事件监听对 async 不生效）
                if url.startswith("sqlite"):
                    await conn.execute(text("PRAGMA journal_mode=WAL"))
                    await conn.execute(text("PRAGMA foreign_keys=ON"))
                    await conn.execute(text("PRAGMA synchronous=NORMAL"))
                    await conn.execute(text("PRAGMA temp_store=MEMORY"))

            self.initialized = True
            logger.info("Database initialized successfully.")

    async def close(self):
        """安全关闭数据库"""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database engine disposed.")
            self.initialized = False

    def get_session_factory(self):
        if not self.initialized:
            raise RuntimeError("Database not initialized")
        return self._session_factory

    async def health_check(self) -> bool:
        """数据库健康检测"""
        if not self.initialized:
            return False

        try:
            async with self._session_factory() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"DB health check failed: {e}")
            return False


db_manager = DatabaseManager()


# ---------------------------------------------------------
# FastAPI Session 依赖（最佳实践）
# ---------------------------------------------------------
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session_factory = db_manager.get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_session_with_ctx() -> AsyncGenerator[AsyncSession, None]:
    session_factory = db_manager.get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
