from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from tradingapi.core.db import db_manager
from tradingapi.repositories.base import BaseRepository

ModelType = TypeVar("ModelType")
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)


class BaseService(Generic[ModelType, RepositoryType], ABC):
    """基础服务类"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._repository = None

    @property
    @abstractmethod
    def repository_class(self) -> Type[RepositoryType]:
        """子类需要实现这个属性，返回对应的Repository类"""
        pass

    @property
    def repository(self) -> RepositoryType:
        """懒加载Repository实例"""
        if self._repository is None:
            self._repository = self.repository_class(self.session)
        return self._repository

    @asynccontextmanager
    async def get_new_session(self):
        """获取新的数据库会话，用于并发操作"""
        session_factory = db_manager.get_session_factory()
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """根据ID获取记录"""
        return await self.repository.get_by_id(id)

    async def get_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[ModelType]:
        """获取所有记录"""
        return await self.repository.get_all(limit=limit, offset=offset)

    async def create(self, **kwargs) -> ModelType:
        """创建记录"""
        return await self.repository.create(**kwargs)

    async def update(self, id: Any, **kwargs) -> Optional[ModelType]:
        """更新记录"""
        return await self.repository.update_by_id(id, **kwargs)

    async def delete(self, id: Any) -> bool:
        """删除记录"""
        return await self.repository.delete_by_id(id)
