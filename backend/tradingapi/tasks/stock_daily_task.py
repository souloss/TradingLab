import asyncio
import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from tradingapi.fetcher import manager
from tradingapi.fetcher.interface import StockInfoFetcher
from tradingapi.repositories.stock_basic_info import (
    StockBasicInfoRepository,
    dataframe_to_stock_data,
)
from tradingapi.repositories.stock_daily_data import StockDailyRepository


async def update_stock_daily(session: AsyncSession):
    basic_repo = StockBasicInfoRepository(session=session)
    daily_repo = StockDailyRepository(session=session)
    stocks = await basic_repo.get_all()
    info_fetcher: StockInfoFetcher = manager.bind(StockInfoFetcher)
    for stock in stocks:
        daily_df = await info_fetcher.fetch_stock_daily_data(
            stock,
            start_date=datetime.datetime.now().date().isoformat().replace("-", ""),
            end_date=datetime.datetime.now().date().isoformat().replace("-", ""),
        )
        daily_repo.upsert_stock_dailys_bydf(daily_df)