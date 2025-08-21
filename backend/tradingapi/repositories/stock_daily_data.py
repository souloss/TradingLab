from datetime import date, datetime
from typing import List, Optional, Sequence

from loguru import logger
import pandas as pd
from sqlalchemy import Column, DateTime, UniqueConstraint, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, SQLModel

from tradingapi.fetcher.interface import OHLCVExtendedSchema
from tradingapi.models.stock_daily_data import StockDailyData
from tradingapi.repositories.base import BaseRepository


class StockDailyRepository(BaseRepository[StockDailyData]):
    """股票每日数据仓库类"""

    model_type = StockDailyData

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_type=self.model_type)

    async def get_daily_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Sequence[StockDailyData]:
        """获取股票每日数据"""
        stmt = select(self.model_type).where(self.model_type.symbol == symbol)
        if start_date:
            stmt = stmt.where(self.model_type.trade_date >= start_date)
        if end_date:
            stmt = stmt.where(self.model_type.trade_date <= end_date)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def upsert_stock_dailys_bydf(self, df:pd.DataFrame):
        datas = dataframe_to_daily_data(df)
        return await self.upsert_many(datas, auto_commit=True)


def dataframe_to_daily_data(df: pd.DataFrame) -> List[StockDailyData]:
    """
    将指定格式的 DataFrame 转换为 StockDailyData 对象列表

    :param df: 包含股票日线数据的 DataFrame
    :return: StockDailyData 对象列表
    """
    # 确保 DataFrame 包含所有必要的列
    required_columns = [
        OHLCVExtendedSchema.timestamp,
        OHLCVExtendedSchema.symbol,
        OHLCVExtendedSchema.open,
        OHLCVExtendedSchema.close,
        OHLCVExtendedSchema.high,
        OHLCVExtendedSchema.low,
        OHLCVExtendedSchema.volume,
        OHLCVExtendedSchema.trading_value,
        OHLCVExtendedSchema.amplitude,
        OHLCVExtendedSchema.pct_change,
        OHLCVExtendedSchema.price_change,
        OHLCVExtendedSchema.turnover_rate,
    ]

    if not all(col in df.columns for col in required_columns):
        missing = [col for col in required_columns if col not in df.columns]
        raise ValueError(f"DataFrame {df.columns}, {df.index} 缺少必要的列: {missing}")

    # # 确保索引是日期类型
    # if not isinstance(df.index, pd.DatetimeIndex):
    #     raise TypeError("DataFrame 索引必须是 DatetimeIndex 类型")

    # 创建存储结果的列表
    daily_data_list = []
    # 遍历 DataFrame 的每一行
    for idx, row in df.iterrows():
        # 将索引转换为日期对象
        # 创建 StockDailyData 对象并添加到列表
        daily_data = StockDailyData(
            symbol=row[OHLCVExtendedSchema.symbol],
            trade_date=row[OHLCVExtendedSchema.timestamp].to_pydatetime().date(),
            open_price=row[OHLCVExtendedSchema.open],
            close_price=row[OHLCVExtendedSchema.close],
            high_price=row[OHLCVExtendedSchema.high],
            low_price=row[OHLCVExtendedSchema.low],
            volume=row[OHLCVExtendedSchema.volume],
            turnover=row[OHLCVExtendedSchema.trading_value],
            amplitude=row[OHLCVExtendedSchema.amplitude],
            change_rate=row[OHLCVExtendedSchema.pct_change],
            change_amount=row[OHLCVExtendedSchema.price_change],
            turnover_rate=row[OHLCVExtendedSchema.turnover_rate],
        )
        daily_data_list.append(daily_data)

    return daily_data_list

def daily_data_to_dataframe(daily_data_list: List[StockDailyData]):
    """
    将 StockDailyData 对象列表转换为指定格式的 DataFrame
    :param daily_data_list: StockDailyData 对象列表
    :return: 格式化后的 DataFrame
    """
    # 创建空列表存储数据
    data = {
        OHLCVExtendedSchema.symbol: [],
        OHLCVExtendedSchema.open: [],
        OHLCVExtendedSchema.close: [],
        OHLCVExtendedSchema.high: [],
        OHLCVExtendedSchema.low: [],
        OHLCVExtendedSchema.volume: [],
        OHLCVExtendedSchema.trading_value: [],
        OHLCVExtendedSchema.amplitude: [],
        OHLCVExtendedSchema.pct_change: [],
        OHLCVExtendedSchema.price_change: [],
        OHLCVExtendedSchema.turnover_rate: [],
    }
    # 日期索引列表
    dates = []

    # 填充数据
    for daily_data in daily_data_list:
        data[OHLCVExtendedSchema.symbol].append(daily_data.symbol)
        data[OHLCVExtendedSchema.open].append(daily_data.open_price)
        data[OHLCVExtendedSchema.close].append(daily_data.close_price)
        data[OHLCVExtendedSchema.high].append(daily_data.high_price)
        data[OHLCVExtendedSchema.low].append(daily_data.low_price)
        data[OHLCVExtendedSchema.amplitude].append(daily_data.amplitude)
        data[OHLCVExtendedSchema.pct_change].append(daily_data.change_rate)
        data[OHLCVExtendedSchema.price_change].append(daily_data.change_amount)
        data[OHLCVExtendedSchema.turnover_rate].append(daily_data.turnover_rate)
        data[OHLCVExtendedSchema.volume].append(daily_data.volume)
        data[OHLCVExtendedSchema.trading_value].append(daily_data.turnover)
        dates.append(daily_data.trade_date)

    # 创建 DataFrame
    df = pd.DataFrame(data)
    # 设置日期索引
    df.index = pd.to_datetime(dates, name=OHLCVExtendedSchema.timestamp)
    # 设置正确的数据类型
    dtypes = {
        OHLCVExtendedSchema.symbol: "object",
        OHLCVExtendedSchema.open: "float64",
        OHLCVExtendedSchema.close: "float64",
        OHLCVExtendedSchema.high: "float64",
        OHLCVExtendedSchema.low: "float64",
        OHLCVExtendedSchema.volume: "int64",
        OHLCVExtendedSchema.trading_value: "float64",
        OHLCVExtendedSchema.amplitude: "float64",
        OHLCVExtendedSchema.pct_change: "float64",
        OHLCVExtendedSchema.price_change: "float64",
        OHLCVExtendedSchema.turnover_rate: "float64",
    }
    for col, dtype in dtypes.items():
        df[col] = df[col].astype(dtype)

    return df
