import asyncio
import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from tradingapi.core.db import get_session_with_ctx
from tradingapi.fetcher.manager import manager
from tradingapi.fetcher.interface import StockInfoFetcher
from tradingapi.repositories.stock_basic_info import (
    StockBasicInfoRepository,
    dataframe_to_stock_data,
)
from tradingapi.repositories.stock_daily_data import StockDailyRepository


async def update_stock_daily():
    async with get_session_with_ctx() as session:
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