from typing import Any, Generic, List, Optional, Sequence, TypeVar, Union

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, inspect
from sqlalchemy.orm.attributes import InstrumentedAttribute

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType]):
    """
    通用仓储类，基于 SQLModel + AsyncSession
    - 支持 SQLite / PostgreSQL
    - 提供 CRUD、批量操作、upsert
    """

    def __init__(self, session: AsyncSession, model_type: type[ModelType]):
        self.session = session
        self.model_type = model_type
        table = inspect(model_type).tables[0]
        self.table = table
        self.pk_columns = [col.name for col in table.primary_key]
        self.db_dialect = session.bind.dialect.name if session.bind else "sqlite"

    def _insert(self):
        """返回数据库对应的 insert 类"""
        return pg_insert if self.db_dialect == "postgresql" else sqlite_insert

    # -------------------- 基础查询 --------------------
    async def get_by_id(self, id_: Any) -> Optional[ModelType]:
        return await self.session.get(self.model_type, id_)

    async def get_all(self) -> Sequence[ModelType]:
        stmt = select(self.model_type)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_count(self) -> int:
        stmt = select(func.count()).select_from(self.model_type)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists(self, **conditions) -> bool:
        stmt = select(func.count()).select_from(self.model_type)
        for field, value in conditions.items():
            stmt = stmt.where(getattr(self.model_type, field) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def get_first(self, **filters: Any) -> Optional[ModelType]:
        stmt = select(self.model_type).where(*self._build_conditions(filters)).limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: Optional[Union[str, Sequence[str]]] = None,
        desc: bool = False,
        keyword: Optional[str] = None,
        keyword_fields: Optional[Sequence[str]] = None,
        **filters: Any,
    ) -> List[ModelType]:
        stmt = select(self.model_type)
        for field, value in filters.items():
            col = getattr(self.model_type, field) if isinstance(field, str) else field
            stmt = stmt.where(col == value)

        if keyword and keyword_fields:
            stmt = stmt.where(
                or_(
                    *[
                        (
                            getattr(self.model_type, f).ilike(f"%{keyword}%")
                            if isinstance(f, str)
                            else f.ilike(f"%{keyword}%")
                        )
                        for f in keyword_fields
                    ]
                )
            )

        if order_by:
            fields = [order_by] if isinstance(order_by, str) else list(order_by)
            stmt = stmt.order_by(
                *[
                    (
                        getattr(self.model_type, f).desc()
                        if desc
                        else getattr(self.model_type, f).asc()
                    )
                    for f in fields
                ]
            )

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    # -------------------- CRUD --------------------
    async def create(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self.session.delete(obj)
        await self.session.commit()

    async def delete_by_id(self, id_: Any) -> bool:
        obj = await self.get_by_id(id_)
        if not obj:
            return False
        await self.delete(obj)
        return True

    # -------------------- UPSERT --------------------
    async def upsert(
        self,
        obj: ModelType,
        conflict_columns: Optional[Sequence[str]] = None,
        update_columns: Optional[Sequence[str]] = None,
    ) -> ModelType:
        if not obj:
            return obj

        conflict_cols = conflict_columns or self.pk_columns
        all_cols = [c.name for c in self.table.columns]
        update_cols = update_columns or [c for c in all_cols if c not in conflict_cols]

        stmt = self._insert()(self.model_type).values(obj.model_dump())
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_={col: getattr(stmt.excluded, col) for col in update_cols},
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return obj

    async def bulk_upsert(
        self,
        objs: List[ModelType],
        conflict_columns: Optional[Sequence[str]] = None,
        update_columns: Optional[Sequence[str]] = None,
        batch_size: int = 1000,
    ) -> List[ModelType]:
        if not objs:
            return objs

        conflict_cols = conflict_columns or self.pk_columns
        all_cols = [c.name for c in self.table.columns]
        update_cols = update_columns or [c for c in all_cols if c not in conflict_cols]

        for i in range(0, len(objs), batch_size):
            chunk = objs[i : i + batch_size]
            stmt = self._insert()(self.model_type).values(
                [o.model_dump() for o in chunk]
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=conflict_cols,
                set_={col: getattr(stmt.excluded, col) for col in update_cols},
            )
            await self.session.execute(stmt)
        await self.session.commit()
        return objs

    # -------------------- 辅助 --------------------
    def _build_conditions(self, filters: dict):
        return [getattr(self.model_type, f) == v for f, v in filters.items()]
