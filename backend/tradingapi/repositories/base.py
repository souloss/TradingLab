from typing import Any, Generic, List, Optional, Sequence, TypeVar, Union

from sqlalchemy import func,select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, inspect

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType]):
    """
    SQLite 专用通用仓储类，基于 SQLModel + AsyncSession
    - 支持对象入参
    - 提供通用 CRUD
    - 批量方法支持 batch_size
    - bulk_upsert 使用 SQLite ON CONFLICT 实现
    """

    def __init__(self, session: AsyncSession, model_type: type[ModelType]):
        self.session = session
        self.model_type = model_type

        # 自动解析表元信息
        table = inspect(model_type).tables[0]
        self.table = table
        self.pk_column = list(table.primary_key.columns)[0]  # 假设单主键
        self.pk_name = self.pk_column.name

    # --------------------
    # 基础查询
    # --------------------
    async def get_by_id(self, id_: Any) -> Optional[ModelType]:
        """根据主键获取记录"""
        return await self.session.get(self.model_type, id_)

    async def get_all(self) -> Sequence[ModelType]:
        """获取所有记录"""
        stmt = select(self.model_type)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_count(self) -> int:
        """获取记录总数"""
        stmt = select(func.count()).select_from(self.model_type)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists(self, **conditions) -> bool:
        """检查是否存在符合条件的记录"""
        stmt = select(func.count()).select_from(self.model_type)
        for field, value in conditions.items():
            stmt = stmt.where(getattr(self.model_type, field) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def get_first(self, **filters: Any) -> Optional[ModelType]:
        """按条件获取第一条记录。"""
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
        **filters: Any,
    ) -> List[ModelType]:
        """
        通用列表查询（支持过滤/排序/分页）。
        - order_by: 字段名或字段名序列
        - desc: 是否倒序（对所有 order_by 字段生效）
        """
        stmt = select(self.model_type).where(*self._build_conditions(filters))

        if order_by:
            fields = [order_by] if isinstance(order_by, str) else list(order_by)
            order_cols = []
            for f in fields:
                if not hasattr(self.model_type, f):
                    raise AttributeError(
                        f"{self.model_type.__name__} 不存在排序字段: {f}"
                    )
                col = getattr(self.model_type, f)
                order_cols.append(col.desc() if desc else col.asc())
            stmt = stmt.order_by(*order_cols)

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # --------------------
    # 单对象 CRUD
    # --------------------
    async def create(self, obj: ModelType) -> ModelType:
        """创建新记录"""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelType) -> ModelType:
        """更新对象（整体替换）"""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ModelType) -> None:
        """删除记录"""
        await self.session.delete(obj)
        await self.session.commit()

    async def delete_by_id(self, id_: Any) -> bool:
        """根据主键删除"""
        obj = await self.get_by_id(id_)
        if obj is None:
            return False
        await self.delete(obj)
        return True

    async def upsert(
        self,
        obj: ModelType,
        conflict_columns: Optional[Sequence[str]] = None,
        update_columns: Optional[Sequence[str]] = None,
    ) -> ModelType:
        """
        SQLite 单条 UPSERT
        - conflict_columns：冲突列，默认主键
        - update_columns：需要更新的列，默认除冲突列外的所有列
        """
        if obj is None:
            return obj

        # 获取表元信息
        table = inspect(self.model_type).tables[0]
        pk_columns = [col.name for col in table.primary_key]

        # 冲突列：用户未传则用主键
        conflict_cols = conflict_columns or pk_columns

        # 可更新列：用户未传则用非冲突列
        all_columns = [col.name for col in table.columns]
        update_cols = update_columns or [
            c for c in all_columns if c not in conflict_cols
        ]

        stmt = insert(self.model_type).values(obj.model_dump())
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_={col: getattr(stmt.excluded, col) for col in update_cols},
        )

        await self.session.execute(stmt)
        await self.session.commit()
        return obj

    # --------------------
    # 批量操作
    # --------------------
    async def bulk_create(
        self, objs: List[ModelType], batch_size: int = 1000
    ) -> List[ModelType]:
        """批量创建"""
        for i in range(0, len(objs), batch_size):
            self.session.add_all(objs[i : i + batch_size])
            await self.session.flush()
        await self.session.commit()
        return objs

    async def bulk_update(
        self, objs: List[ModelType], batch_size: int = 1000
    ) -> List[ModelType]:
        """批量更新"""
        for i in range(0, len(objs), batch_size):
            self.session.add_all(objs[i : i + batch_size])
            await self.session.flush()
        await self.session.commit()
        return objs

    async def bulk_upsert(
        self,
        objs: List[ModelType],
        conflict_columns: Optional[Sequence[str]] = None,
        update_columns: Optional[Sequence[str]] = None,
        batch_size: int = 1000,
    ) -> List[ModelType]:
        """
        SQLite 批量 UPSERT（改进版）
        - 避免手写 SQL，使用 SQLAlchemy insert().on_conflict_do_update()
        - conflict_columns：指定冲突列（默认主键）
        - update_columns：指定需要更新的列（默认除冲突列外的所有列）
        """

        if not objs:
            return objs

        # 获取表元信息
        table = inspect(self.model_type).tables[0]
        pk_columns = [col.name for col in table.primary_key]

        # 冲突列：用户未传则用主键
        conflict_cols = conflict_columns or pk_columns
        # 可更新列：用户未传则用 非冲突列
        all_columns = [col.name for col in table.columns]
        update_cols = update_columns or [c for c in all_columns if c not in conflict_cols]

        for i in range(0, len(objs), batch_size):
            chunk = objs[i : i + batch_size]
            stmt = insert(self.model_type).values([obj.model_dump() for obj in chunk])
            stmt = stmt.on_conflict_do_update(
                index_elements=conflict_cols,
                set_={col: getattr(stmt.excluded, col) for col in update_cols},
            )
            await self.session.execute(stmt)

        await self.session.commit()
        return objs
