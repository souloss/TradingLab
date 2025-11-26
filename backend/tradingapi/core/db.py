# app/core/db.py
import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, QueuePool, StaticPool
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel

from .config import app_config


# OPTIMIZATION: Enhanced database configuration
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance and reliability"""
    cursor = dbapi_connection.cursor()
    # OPTIMIZATION: Enable WAL mode for better concurrency
    cursor.execute("PRAGMA journal_mode=WAL")
    # OPTIMIZATION: Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys=ON")
    # OPTIMIZATION: Set synchronous mode for better performance
    cursor.execute("PRAGMA synchronous=NORMAL")
    # OPTIMIZATION: Set cache size (negative value means KB)
    cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
    # OPTIMIZATION: Set temp store to memory
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.close()

class DatabaseManager:
    """数据库管理器 - 单例模式，优化异步性能"""

    _instance: Optional['DatabaseManager'] = None
    _engine = None
    _session_factory = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self._connection_count = 0
            self.initialized = False

    async def initialize(self) -> None:
        """初始化数据库连接 - 优化连接池和性能配置"""
        if self._engine is not None:
            return

        async with self._lock:
            if self._engine is not None:
                return

            try:
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

                # OPTIMIZATION: Enhanced engine configuration
                engine_kwargs = {
                    "echo": app_config.DEBUG,
                    "future": True,
                }
                
                # OPTIMIZATION: Different pool configurations for different databases
                if "sqlite" in app_config.DATABASE_URL:
                    engine_kwargs.update({
                        "poolclass": NullPool,
                        "connect_args": {
                            "check_same_thread": False,
                            "timeout": 30,  # 30 second timeout
                        },
                    })
                else:
                    # For PostgreSQL/MySQL
                    engine_kwargs.update({
                        "poolclass": QueuePool,
                        "pool_size": 10,
                        "max_overflow": 20,
                        "pool_pre_ping": True,
                        "pool_recycle": 3600,  # Recycle connections every hour
                    })

                # 创建引擎
                self._engine = create_async_engine(app_config.DATABASE_URL, **engine_kwargs)

                # OPTIMIZATION: Enhanced session factory configuration
                self._session_factory = async_sessionmaker(
                    bind=self._engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autoflush=True,  # Auto flush for better consistency
                    autocommit=False,
                )

                # SECURITY: Create tables with proper error handling
                async with self._engine.begin() as conn:
                    await conn.run_sync(SQLModel.metadata.create_all)
                    logger.info("Database tables created")

                self.initialized = True
                logger.info(f"Database initialized: {app_config.DATABASE_URL}")

            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                self.initialized = False
                raise

    async def close(self) -> None:
        """关闭数据库连接 - 优雅关闭"""
        if self._engine:
            try:
                # OPTIMIZATION: Graceful shutdown with connection cleanup
                await self._engine.dispose()
                logger.info(f"Database engine disposed. Total connections used: {self._connection_count}")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self._engine = None
                self._session_factory = None
                self.initialized = False
                self._connection_count = 0

    def get_session_factory(self):
        """获取会话工厂 - 带连接计数"""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._session_factory
    
    async def health_check(self) -> bool:
        """数据库健康检查"""
        if not self.initialized or not self._engine:
            return False
        try:
            session_factory = self.get_session_factory()
            async with session_factory() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_connection_info(self) -> dict:
        """获取连接信息用于监控"""
        if not self._engine:
            return {"status": "not_initialized"}
        
        pool = self._engine.pool
        return {
            "status": "initialized" if self.initialized else "not_initialized",
            "pool_size": getattr(pool, 'size', 0),
            "checked_in": getattr(pool, 'checkedin', 0),
            "checked_out": getattr(pool, 'checkedout', 0),
            "overflow": getattr(pool, 'overflow', 0),
            "total_connections": self._connection_count
        }


# 全局数据库管理器实例
db_manager = DatabaseManager()


# OPTIMIZATION: Enhanced session dependency with better error handling
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖注入函数 - 优化异常处理和连接管理"""
    if not db_manager.initialized:
        raise RuntimeError("Database not initialized")
        
    session_factory = db_manager.get_session_factory()
    session = None
    
    try:
        session = session_factory()
        db_manager._connection_count += 1
        yield session
        # OPTIMIZATION: Explicit commit for successful operations
        await session.commit()
        
    except Exception as e:
        if session:
            try:
                await session.rollback()
                logger.warning(f"Session rolled back due to error: {e}")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback session: {rollback_error}")
        raise
        
    finally:
        if session:
            try:
                await session.close()
            except Exception as close_error:
                logger.error(f"Failed to close session: {close_error}")


# 新增：自动提交的 get_session 函数
@asynccontextmanager
async def get_session_with_ctx() -> AsyncGenerator[AsyncSession, None]:
    """获取自动提交的数据库会话 - 优化事务管理"""
    if not db_manager.initialized:
        raise RuntimeError("Database not initialized")
        
    session_factory = db_manager.get_session_factory()
    session = None
    
    try:
        session = session_factory()
        db_manager._connection_count += 1
        yield session
        # OPTIMIZATION: Explicit commit with better error handling
        await session.commit()
        logger.debug("Session committed successfully")
        
    except Exception as e:
        if session:
            try:
                await session.rollback()
                logger.warning(f"Session rolled back in context manager: {e}")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback in context manager: {rollback_error}")
        raise
        
    finally:
        if session:
            try:
                await session.close()
            except Exception as close_error:
                logger.error(f"Failed to close session in context manager: {close_error}")
