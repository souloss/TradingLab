import asyncio
import datetime

import akshare as ak
import pandas as pd
from loguru import logger

from tradingapi.fetcher.interface import OHLCVExtendedSchema
from tradingapi.models.stock_basic_info import StockBasicInfo

from ..base import DataSourceName, StockDataSource
from ..manager import manager
from .exchange import fetch_bj_stocks, fetch_sh_stocks, fetch_sz_stocks


@manager.register_data_source
class Sina(StockDataSource):
    """新浪数据源"""

    name = DataSourceName.Sina

    def __init__(self):
        super().__init__()

    async def health_check(self) -> bool:
        """检查数据源是否可用"""
        try:
            df = await asyncio.wait_for(
                asyncio.to_thread(
                    ak.stock_zh_a_daily,
                    start_date=datetime.datetime.now()
                    .date()
                    .isoformat()
                    .replace("-", ""),
                    end_date=datetime.datetime.now()
                    .date()
                    .isoformat()
                    .replace("-", ""),
                ),
                timeout=self.timeout,
            )
            return True
        except Exception as ex:
            logger.error(f"健康检查失败, exception:{ex}")
            return False

    def normalization(self, df: pd.DataFrame, symbol:str) -> pd.DataFrame:
        # 1手=100股
        df = df.rename(
            columns={
                "date": OHLCVExtendedSchema.timestamp,
                "open": OHLCVExtendedSchema.open,
                "close": OHLCVExtendedSchema.close,
                "high": OHLCVExtendedSchema.high,
                "low": OHLCVExtendedSchema.low,
                "amount": OHLCVExtendedSchema.trading_value,
                "turnover": OHLCVExtendedSchema.turnover_rate,
            }
        )
        # 目标Schema的所有列
        required_columns = list(OHLCVExtendedSchema.to_schema().columns.keys())

        # 步骤2：填充缺失列（用NaN）
        for col in required_columns:
            if col not in df.columns:
                df[col] = 0

        df[OHLCVExtendedSchema.symbol] = symbol
        df = df.set_index(OHLCVExtendedSchema.timestamp)
        df = df.reindex(columns=list(OHLCVExtendedSchema.to_schema().columns.keys()))

        return OHLCVExtendedSchema.validate(df)

    @manager.register_method(weight=1.2, max_requests_per_minute=30, max_concurrent=5)
    async def fetch_stock_daily_data(
        self, stock: StockBasicInfo, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        参数:
            stock.symbol: 股票代码
            start_date: 开始日期 (格式 'YYYYMMDD')
            end_date: 结束日期 (格式 'YYYYMMDD')

        返回:
            包含股票数据的 DataFrame，如果无数据则返回空 DataFrame
        """
        start_date = start_date.replace("-", "")
        end_date = end_date.replace("-", "")
        logger.info(f"获取数据: {stock.symbol} ({start_date} 至 {end_date})")

        try:
            # akshare 是同步的，这里用 to_thread 包装成异步
            df = await asyncio.to_thread(
                ak.stock_zh_a_daily,
                symbol=stock.exchange.lower() + stock.symbol,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )

            if df.empty:
                logger.info(f"空数据: {stock.symbol} ({start_date} 至 {end_date})")
                return pd.DataFrame()

            df = self.normalization(df, stock.symbol)
            logger.success(f"成功获取: {stock.symbol} ({len(df)}条记录)")
            return df

        except Exception as e:
            logger.error(f"数据获取失败: {stock.symbol} - {str(e)}")
            return pd.DataFrame()
