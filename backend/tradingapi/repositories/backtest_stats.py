from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tradingapi.models.backtest_stats import BacktestStatsTable
from tradingapi.repositories.base import BaseRepository
from tradingapi.schemas.backtest import BacktestListItem
from tradingapi.schemas.response import PaginatedResponse


class BacktestStatsRepository(BaseRepository[BacktestStatsTable]):
    """回测统计仓库类"""

    model_type = BacktestStatsTable

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_type=self.model_type)

    async def list_paged(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
    ) -> PaginatedResponse[BacktestListItem]:
        offset = (page - 1) * page_size

        objs = await super().list(
            offset=offset,
            limit=page_size,
            order_by="id",
            desc=True,
            keyword=keyword,
            keyword_fields=[
                BacktestStatsTable.stock_code,
                BacktestStatsTable.stock_name,
            ],
        )

        # count 语句同样要处理 keyword
        stmt = select(func.count()).select_from(BacktestStatsTable)
        if keyword:
            stmt = stmt.where(
                BacktestStatsTable.stock_code.ilike(f"%{keyword}%")
                | BacktestStatsTable.stock_name.ilike(f"%{keyword}%")
            )
        result = await self.session.execute(stmt)
        total = result.scalar_one()

        items = [BacktestListItem.model_validate(o) for o in objs]

        return PaginatedResponse[BacktestListItem](
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )
