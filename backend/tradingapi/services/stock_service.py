from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from tradingapi.models import StockBasicInfo
from tradingapi.repositories.stock_basic_info import StockBasicInfoRepository
from tradingapi.schemas.stocks import (StockBasicInfoFilter,
                                       StockBasicInfoLiteSchema,
                                       StockBasicInfoSchema)


class StocksService:
    def __init__(self, session: AsyncSession):
        self.repo = StockBasicInfoRepository(session)

    async def list_all(self) -> List[StockBasicInfoSchema]:
        objs = await self.repo.list()
        return [StockBasicInfoSchema.model_validate(o) for o in objs]

    async def filter_stock(
        self, filter: StockBasicInfoFilter
    ) -> List[StockBasicInfoSchema]:
        objs = await self.repo.advanced_filter(
            exchanges=filter.exchange,
            sections=filter.sections,
            stock_types=filter.stock_type,
            industries=filter.industries,
            start_listing_date=filter.start_listing_date,
            end_listing_date=filter.end_listing_date,
            min_float_market_value=filter.min_market_cap,
            max_float_market_value=filter.max_market_cap,
        )
        return [StockBasicInfoSchema.model_validate(o) for o in objs]

    async def get_filter_options(self) -> Dict[str, List[str]]:
        ret = await self.repo.get_filter_options()
        return ret

    async def get_stock_name_by_code(self, code: str) -> str:
        name = await self.repo.get_stock_name_by_symbol(code)
        return name
