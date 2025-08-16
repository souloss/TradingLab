import asyncio
import datetime

import tradingapi.fetcher.datasources
from tradingapi.fetcher.base import DataSourceName
from tradingapi.fetcher.interface import StockInfoFetcher
from tradingapi.fetcher.manager import manager


async def main():
    # 初始化所有数据源注册
    # (这通常在应用启动时完成)
    manager.complete_registration()

    info_api: StockInfoFetcher = manager.bind(StockInfoFetcher)
    stocks = info_api.fetch_stock_data(
        "300001", start_date="20250801", end_date="20250801"
    )
    print(stocks)


if __name__ == "__main__":
    asyncio.run(main())
