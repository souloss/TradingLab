# models/base.py
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

import pandas as pd
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from sqlalchemy import Sequence, and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(SQLAlchemyAsyncRepository[ModelType], Generic[ModelType]):
    """基础仓储类，提供通用的CRUD操作"""

    def __init__(self, session: AsyncSession, model_type: Type[ModelType]):
        super().__init__(session=session, model_type=model_type)
        self.model_type = model_type

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """根据ID获取单个记录"""
        return await self.get(id)

    async def get_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> Sequence[ModelType]:
        """获取所有记录"""
        return await self.list(limit=limit, offset=offset)

    async def get_count(self) -> int:
        """获取记录总数"""
        stmt = select(func.count()).select_from(self.model_type)
        result = await self.session.execute(stmt)
        return result.scalar()

    async def create_model(self, **kwargs) -> ModelType:
        """创建新记录"""
        return await self.add(self.model_type(**kwargs))

    async def update_by_id(self, id: Any, **kwargs) -> Optional[ModelType]:
        """根据ID更新记录"""
        return await self.update(id, **kwargs)

    async def delete_by_id(self, id: Any) -> bool:
        """根据ID删除记录"""
        try:
            await self.delete(id)
            return True
        except Exception:
            return False

    async def bulk_create(self, items: List[Dict[str, Any]]) -> List[ModelType]:
        """批量创建"""
        models = [self.model_type(**item) for item in items]
        self.session.add_all(models)
        await self.session.flush()
        return models

    async def bulk_update(
        self, updates: List[Dict[str, Any]], id_field: str = "id"
    ) -> int:
        """批量更新"""
        if not updates:
            return 0
        stmt = update(self.model_type)
        # 按ID分组更新
        for update_data in updates:
            id_value = update_data.pop(id_field)
            update_stmt = stmt.where(
                getattr(self.model_type, id_field) == id_value
            ).values(**update_data)
            await self.session.execute(update_stmt)
        return len(updates)

    async def exists(self, **conditions) -> bool:
        """检查记录是否存在"""
        stmt = select(func.count()).select_from(self.model_type)
        for field, value in conditions.items():
            stmt = stmt.where(getattr(self.model_type, field) == value)
        result = await self.session.execute(stmt)
        return result.scalar() > 0
