from sqlalchemy.ext.asyncio import AsyncSession

from tradingapi.fetcher.manager import manager
from tradingapi.fetcher.interface import StockInfoFetcher
from tradingapi.repositories.stock_basic_info import StockBasicInfoRepository, dataframe_to_stock_data


async def update_stock_basic_info(session: AsyncSession):
    repo = StockBasicInfoRepository(session=session)
    stock_fetcher: StockInfoFetcher = manager.bind(StockInfoFetcher)
    stock_info = await stock_fetcher.get_all_stock_basic_info()
    await repo.upsert_many(
        dataframe_to_stock_data(stock_info), match_fields=["symbol"], auto_commit=True
    )
