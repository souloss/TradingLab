from datetime import datetime

from tradingapi.core.db import get_session_with_ctx
from tradingapi.fetcher.datasources.exchange import fetch_all_stocks
from tradingapi.fetcher.interface import StockInfoFetcher
from tradingapi.fetcher.manager import manager
from tradingapi.models.stock_basic_info import StockBasicInfo
from tradingapi.repositories.stock_basic_info import StockBasicInfoRepository


async def update_stock_basic_info():
    async with get_session_with_ctx() as session:
        repo = StockBasicInfoRepository(session=session)
        stock_fetcher: StockInfoFetcher = manager.bind(StockInfoFetcher)
        all_stocks = await fetch_all_stocks()
        for _, stock in all_stocks.iterrows():
            stock_detail = await stock_fetcher.get_stock_basic_info(
                stock["交易所"], stock["证券代码"]
            )
            if not stock_detail:
                continue
            stock_detail["股票类型"] = stock["股票类型"]
            stock_detail["板块"] = stock["板块"]

            print(stock_detail.get("上市时间"), type(stock_detail.get("上市时间")))

            stock_basic_info = StockBasicInfo(
                symbol=stock_detail.get("证券代码"),
                exchange=stock_detail.get("交易所"),
                section=stock_detail.get("板块"),
                stock_type=stock_detail.get("股票类型"),
                name=stock_detail.get("名称"),
                listing_date=(
                    datetime.fromisoformat(stock_detail.get("上市时间")).date()
                    if stock_detail.get("上市时间")
                    else ""
                ),
                industry=stock_detail.get("行业"),
                total_shares=stock_detail.get("总股本"),
                float_shares=stock_detail.get("流通股本"),
                total_market_value=stock_detail.get("总市值"),
                float_market_value=stock_detail.get("流通市值"),
            )
            await repo.upsert(
                stock_basic_info, conflict_columns=[StockBasicInfo.symbol]
            )
