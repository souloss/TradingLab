# app/services/backtest_service.py
import asyncio
import math
from datetime import datetime, timedelta
from typing import List

from backtesting import Backtest
from chinese_calendar import is_holiday
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from tradingapi.fetcher.interface import OHLCVExtendedSchema
from tradingapi.models.backtest_stats import BacktestStatsTable
from tradingapi.repositories.backtest_stats import BacktestStatsRepository
from tradingapi.schemas.backtest import (
    BacktestListItem,
    BacktestRequest,
    BacktestResponse,
    BacktestResultItem,
    BacktestResults,
    ChartData,
    TradeType,
)
from tradingapi.schemas.response import PaginatedResponse
from tradingapi.services.base import BaseService
from tradingapi.strategyv2.model import parse_backtest_result
from tradingapi.strategyv2.strategy import StrategyMap

from tradingapi.services.stock_daily_service import StockDailyService
from tradingapi.services.stock_service import StocksService


class BacktestService(BaseService[BacktestStatsTable, BacktestStatsRepository]):

    @property
    def repository_class(self):
        return BacktestStatsRepository

    def __init__(self, session: AsyncSession):
        self.repo = BacktestStatsRepository(session)
        self.daily_service = StockDailyService(session=session)
        self.stock_service = StocksService(session=session)

    async def list_paged(
        self, page: int = 1, page_size: int = 20, keyword: str | None = None
    ) -> PaginatedResponse[BacktestListItem]:
        objs = await self.repo.list_paged(page=page, page_size=page_size, keyword=keyword)
        return objs

    # 获取所有回测结果
    async def list_all(self) -> List[BacktestResponse]:
        objs = await self.repo.list()
        return [BacktestResponse.model_validate(o) for o in objs]

    # 根据ID获取回测结果
    async def get_by_id(self, id) -> BacktestResponse:
        ret = await self.repo.get_by_id(id)
        resp = BacktestResponse(
            id=ret.id,
            stockCode=ret.stock_code,
            stockName=ret.stock_name,
            chartData=[ChartData(**ep) for ep in ret.chart_data],
            backtestStats=ret.to_pydantic(),
        )
        return resp

    # 个股回测
    async def backtest(self, req: BacktestRequest) -> BacktestResponse:
        ...
        stock = await self.stock_service.get_stock_by_code(req.stock_code)
        if not stock:
            raise Exception("股票基本信息为空，请加载股票基本信息后回测!")
        # 获取数据
        df = await self.daily_service.get_daily_by_code(
            stock, req.start_date, req.end_date
        )
        if df.empty:
            logger.warning(f"{req.model_dump()} 请求回测，日线数据为空")
            return None

        backtest_df = df.rename(
            columns={
                OHLCVExtendedSchema.open: "Open",
                OHLCVExtendedSchema.high: "High",
                OHLCVExtendedSchema.low: "Low",
                OHLCVExtendedSchema.close: "Close",
                OHLCVExtendedSchema.volume: "Volume",
            }
        )[["Open", "High", "Low", "Close", "Volume"]]

        strategy = StrategyMap.get(req.strategy.type)

        if not strategy:
            raise Exception(f"策略 {req.strategy.type} 不存在")
        bt = Backtest(
            backtest_df, strategy, cash=100000, commission=0.002, finalize_trades=True
        )
        stats = None
        if req.strategy.optimize:
            stats = bt.optimize(
                maximize="Equity Final [$]",
                **strategy.optimization_space(),
                constraint=strategy.constraint(),
            )
        else:
            stats = bt.run(**req.strategy.parameters.model_dump())
        if stats is not None or not stats.empty:
            logger.debug(f"回测结果:\n{stats}\n策略为:{stats._strategy}")
            # 准备图表数据
            chart_data = []
            known_columns = [
                OHLCVExtendedSchema.open,
                OHLCVExtendedSchema.high,
                OHLCVExtendedSchema.low,
                OHLCVExtendedSchema.close,
                OHLCVExtendedSchema.volume,
                OHLCVExtendedSchema.symbol,
            ]
            chart_data = [
                ChartData(
                    chart_date=date.to_pydatetime(),
                    open=row[OHLCVExtendedSchema.open],
                    high=row[OHLCVExtendedSchema.high],
                    low=row[OHLCVExtendedSchema.low],
                    close=row[OHLCVExtendedSchema.close],
                    volume=row[OHLCVExtendedSchema.volume],
                    extra_fields=row.drop(known_columns).to_dict(),  # 未知列转字典
                )
                for date, row in df.iterrows()
            ]
            backtest_stats = parse_backtest_result(stats)
            record = BacktestStatsTable.from_pydantic(
                stock.symbol, stock.name, chart_data=chart_data, stats=backtest_stats
            )
            added_instance = await self.repo.create(record)
            if backtest_stats.sqn == math.nan:
                backtest_stats.sqn = None
            resp = BacktestResponse(
                id=added_instance.id,
                stock_code=stock.symbol,
                stock_name=stock.name,
                chart_data=chart_data,
                backtest_stats=backtest_stats,
            )
            return resp

    async def backtest_batch(
        self, reqs: List[BacktestRequest], max_concurrent=50
    ) -> BacktestResults:
        ...
        results = []
        # 使用信号量控制并发数量
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_backtest(req):
            async with semaphore:
                async with self.get_new_session() as new_session:
                    service = BacktestService(new_session)
                    return await service.backtest(req)

        # 创建任务列表
        tasks = [run_backtest(req) for req in reqs]
        # 等待所有任务完成
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                # 处理异常情况
                logger.error(f"Backtest failed with error: {response}")
                continue

            if response is None:
                continue

            # 获取对应的请求
            req = reqs[i]
            end_date = req.end_date

            # 计算买入和卖出次数
            buy_count = sum(
                1
                for trade in response.backtest_stats.trades
                if trade.entry_time == datetime.today()
            )
            sell_count = sum(
                1
                for trade in response.backtest_stats.trades
                if trade.exit_time == datetime.today()
            )

            # 确定目标日期（交易日）
            target_date = None

            # 检查end_date是否是交易日
            if not is_holiday(end_date):  # 假设有is_holiday方法判断是否是交易日
                target_date = end_date
            else:
                max_days_to_check = 30  # 最多向前检查30天
                current_date = end_date
                for _ in range(max_days_to_check):
                    if not is_holiday(current_date):
                        target_date = current_date
                    current_date -= timedelta(days=1)

            # 如果没有找到交易日，则使用HOLD信号
            signal_type = TradeType.HOLD

            # 如果找到了交易日，检查该日期的交易信号
            if target_date is not None:
                # 获取该日期的所有交易记录
                day_trades = [
                    t
                    for t in response.backtest_stats.trades
                    if t.exit_time == target_date or t.entry_time == target_date
                ]
                if day_trades:
                    # 按时间排序，取最后一条交易记录的类型作为信号
                    day_trades_sorted = sorted(day_trades, key=lambda x: x.entry_time)
                    signal_type = (
                        TradeType.BUY
                        if day_trades_sorted[-1].entry_time == datetime.today()
                        else TradeType.SELL
                    )

            # 创建回测结果项
            result_item = BacktestResultItem(
                stockCode=response.stock_code,
                backtestId=response.id,
                stock_return=response.backtest_stats.return_pct,
                signalType=signal_type,
                buyCount=buy_count,
                sellCount=sell_count,
            )
            results.append(result_item)

        return results
