# app/services/backtest_service.py
import asyncio
import json
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from typing import List

import pandas as pd
from chinese_calendar import is_holiday
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from tradingapi.fetcher.interface import OHLCVExtendedSchema, StockInfoFetcher
from tradingapi.repositories.stock_basic_info import dataframe_to_stock_data
from tradingapi.fetcher.manager import manager
from tradingapi.models import BacktestResult
from tradingapi.repositories.backtest_result import BacktestResultRepository
from tradingapi.schemas.backtest import (BacktestRequest, BacktestResponse,
                                         BacktestResultItem, BacktestResults,
                                         ChartData, SelectStockBacktestReq,
                                         Trade, TradeType)
from tradingapi.services.base import BaseService
from tradingapi.strategy.manager import StrategyConfig, create_signal_manager

from .stock_daily_service import StockDailyService
from .stock_service import StocksService


class BacktestService(BaseService[BacktestResult, BacktestResultRepository]):

    @property
    def repository_class(self):
        return BacktestResultRepository

    def __init__(self, session: AsyncSession):
        self.repo = BacktestResultRepository(session)
        self.daily_service = StockDailyService(session=session)
        self.stock_service = StocksService(session=session)

    # 获取所有回测结果
    async def list_all(self) -> List[BacktestResponse]:
        objs = await self.repo.list()
        return [BacktestResponse.model_validate(o) for o in objs]

    # 根据ID获取回测结果
    async def get_by_id(self, id) -> BacktestResponse:
        return await self.repo.get(id)

    # 个股回测
    async def backtest(self, req: BacktestRequest) -> BacktestResponse:
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

        # 创建信号管理器和生成信号
        signal_mgr = create_signal_manager()
        for strategy_item in req.strategies:
            logger.debug(
                f"使用策略: {strategy_item}, 参数: {strategy_item.parameters}, to: {strategy_item.parameters.to_strategies_config().to_dict()}"
            )
            signal_mgr.add_strategy(
                StrategyConfig(
                    name=strategy_item.type,
                    parameters=strategy_item.parameters.to_strategies_config().to_dict(),
                )
            )
        # 生成信号
        df = signal_mgr.generate_signals(df)
        # 执行回测策略
        initial_capital = 100000
        try:
            final_capital, trades_df = backtest_strategy(df)
        except Exception as ex:
            logger.error(f"回测异常：df:{df}")
            raise ex
        # 计算总收益率
        stock_return = (final_capital - initial_capital) / initial_capital
        # 准备交易记录数据
        trades = []
        for _, row in trades_df.iterrows():
            trade_type = TradeType.BUY if row["类型"] == "买入" else TradeType.SELL
            trades.append(
                Trade(
                    trade_date=row[OHLCVExtendedSchema.timestamp].to_pydatetime(),
                    type=trade_type,
                    price=row["价格"],
                    quantity=row["股数"],
                    commission=row["手续费"],
                    marketValue=row["持仓市值"],
                    cashBalance=row["现金余额"],
                )
            )
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
        # 获取股票名称
        stock_name = await self.stock_service.get_stock_name_by_code(req.stock_code)
        if not stock_name:
            raise Exception(f"stock: {req.stock_code} not exist!")

        # 构建回测结果对象（核心实现）
        backtest_result = BacktestResult(
            stock_code=req.stock_code,
            stock_name=stock_name,
            start_date=datetime.combine(
                req.start_date, datetime.min.time()
            ),  # date转datetime
            end_date=datetime.combine(req.end_date, datetime.min.time()),
            strategies=[s.model_dump(mode="json") for s in req.strategies],
            stock_return=stock_return,
            trade_count=len(trades),
            trades=[t.model_dump(mode="json") for t in trades],  
            chart_data=[c.model_dump(mode="json")for c in chart_data],
            )
        added_instance = await self.repo.add(
            backtest_result, auto_commit=True
        )  # 添加到会话
        resp = BacktestResponse.model_validate(added_instance)  # ✅ 直接可用
        return resp

    async def backtest_batch(
        self, reqs: List[BacktestRequest], max_concurrent=10
    ) -> BacktestResults:
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
                1 for trade in response.trades if trade.type == TradeType.BUY
            )
            sell_count = sum(
                1 for trade in response.trades if trade.type == TradeType.SELL
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
                    t for t in response.trades if t.trade_date.date() == target_date
                ]
                if day_trades:
                    # 按时间排序，取最后一条交易记录的类型作为信号
                    day_trades_sorted = sorted(day_trades, key=lambda x: x.trade_date)
                    signal_type = day_trades_sorted[-1].type.value

            # 创建回测结果项
            result_item = BacktestResultItem(
                stockCode=response.stock_code,
                backtestId=response.id,
                stock_return=response.stock_return,
                signalType=signal_type,
                buyCount=buy_count,
                sellCount=sell_count,
            )
            results.append(result_item)

        return results


def backtest_strategy(
    df,
    initial_capital=100000,
    commission_rate=0.0003,
    tax_rate=0.001,
    slippage=0.001,
    buy_threshold=0.5,
    sell_threshold=-0.5,
    position_ratio=0.95,
):
    position = 0  # 0:空仓 1:持仓
    capital = initial_capital
    shares = 0
    trades = []

    # 预提取数据提高效率
    close_prices = df[OHLCVExtendedSchema.close].values
    signals = df["Signal_Combined"].values
    dates = df.index

    for i in range(0, len(df)):
        current_signal = signals[i]
        price = close_prices[i]

        # 买入逻辑
        if not position and current_signal >= buy_threshold:
            # 计算实际买入价（含滑点）
            buy_price = price * (1 + slippage)

            # 计算可买股数（保留最少现金）
            max_shares = int((capital * position_ratio) // buy_price)
            if max_shares > 0:
                shares = max_shares
                trade_cost = shares * buy_price
                commission = trade_cost * commission_rate

                capital -= trade_cost + commission
                position = 1

                trades.append(
                    {
                        OHLCVExtendedSchema.timestamp: dates[i],
                        "类型": "买入",
                        "价格": buy_price,
                        "股数": shares,
                        "手续费": commission,
                        "持仓市值": shares * price,
                        "现金余额": capital,
                    }
                )

        # 卖出逻辑
        elif position and current_signal <= sell_threshold:
            # 计算实际卖出价（含滑点）
            sell_price = price * (1 - slippage)
            trade_amount = shares * sell_price
            commission = trade_amount * commission_rate
            tax = trade_amount * tax_rate

            capital += trade_amount - commission - tax
            position = 0

            trades.append(
                {
                    OHLCVExtendedSchema.timestamp: dates[i],
                    "类型": "卖出",
                    "价格": sell_price,
                    "股数": shares,
                    "手续费": commission + tax,
                    "持仓市值": 0,
                    "现金余额": capital,
                }
            )
            shares = 0

    # 处理最终持仓
    if position:
        sell_price = close_prices[-1] * (1 - slippage)
        trade_amount = shares * sell_price
        commission = trade_amount * commission_rate
        tax = trade_amount * tax_rate
        capital += trade_amount - commission - tax

        trades.append(
            {
                OHLCVExtendedSchema.timestamp: dates[-1],
                "类型": "平仓",
                "价格": sell_price,
                "股数": shares,
                "手续费": commission + tax,
                "持仓市值": 0,
                "现金余额": capital,
            }
        )

    return capital, pd.DataFrame(trades)
