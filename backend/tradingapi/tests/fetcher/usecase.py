import asyncio

from backtesting import Backtest

from tradingapi.fetcher.interface import StockInfoFetcher
from tradingapi.fetcher.manager import manager
from tradingapi.models.stock_basic_info import StockBasicInfo
from tradingapi.strategyv2.strategy import *


async def main():
    # 初始化所有数据源注册
    # (这通常在应用启动时完成)
    manager.complete_registration()
    stock = StockBasicInfo(exchange="SZ", symbol="603779")
    info_api: StockInfoFetcher = manager.bind(StockInfoFetcher)
    # from tradingapi.fetcher.datasources.eastmoney import EASTMONEY

    # for i in range(5):
    #     stocks = await info_api.fetch_stock_daily_data(
    #         stock, start_date="20250801", end_date="20250810"
    #     )
    #     print(stocks)

    stocks = await info_api.fetch_stock_daily_data(
        stock, start_date="20240826", end_date="20250822"
    )
    stocks = stocks.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )[["Open", "High", "Low", "Close", "Volume"]]
    print(stocks)

    for strategyv in [
        VolumeSpikeStrategy,
        MAStrategy,
        MACDStrategy,
        ATRMeanReversionStrategy,
    ]:
        bt = Backtest(
            stocks, strategyv, cash=100000, commission=0.002, finalize_trades=True
        )
        s = bt.run()
        # import pprint
        # pprint.pprint(strategyv)
        # pprint.pprint(stats)
        # pprint.pprint(parse_backtest_result(stats).__dict__, width=120)
        # s = bt.optimize(
        #     maximize="Equity Final [$]",
        #     **strategyv.optimization_space(),
        #     constraint=strategyv.constraint(),
        # )
        print(s["_strategy"])
        print(s)


if __name__ == "__main__":
    asyncio.run(main())
