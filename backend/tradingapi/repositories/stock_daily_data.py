from datetime import date, datetime
from typing import List, Optional, Sequence

import pandas as pd
from sqlalchemy import Column, DateTime, UniqueConstraint, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, SQLModel

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


def daily_data_to_dataframe(daily_data_list: List[StockDailyData]):
    """
    将 StockDailyData 对象列表转换为指定格式的 DataFrame
    :param daily_data_list: StockDailyData 对象列表
    :return: 格式化后的 DataFrame
    """
    # 创建空列表存储数据
    data = {
        "股票代码": [],
        "开盘": [],
        "收盘": [],
        "最高": [],
        "最低": [],
        "成交量": [],
        "成交额": [],
        "振幅": [],
        "涨跌幅": [],
        "涨跌额": [],
        "换手率": [],
    }
    # 日期索引列表
    dates = []

    # 填充数据
    for daily_data in daily_data_list:
        data["股票代码"].append(daily_data.symbol)
        data["开盘"].append(daily_data.open_price)
        data["收盘"].append(daily_data.close_price)
        data["最高"].append(daily_data.high_price)
        data["最低"].append(daily_data.low_price)
        data["振幅"].append(daily_data.amplitude)
        data["涨跌幅"].append(daily_data.change_rate)
        data["涨跌额"].append(daily_data.change_amount)
        data["换手率"].append(daily_data.turnover_rate)
        data["成交量"].append(daily_data.volume)
        data["成交额"].append(daily_data.turnover)
        dates.append(daily_data.trade_date)

    # 创建 DataFrame
    df = pd.DataFrame(data)
    # 设置日期索引
    df.index = pd.DatetimeIndex(dates, name="日期")
    # 设置正确的数据类型
    dtypes = {
        "股票代码": "object",
        "开盘": "float64",
        "收盘": "float64",
        "最高": "float64",
        "最低": "float64",
        "成交量": "int64",
        "成交额": "float64",
        "振幅": "float64",
        "涨跌幅": "float64",
        "涨跌额": "float64",
        "换手率": "float64",
    }
    for col, dtype in dtypes.items():
        df[col] = df[col].astype(dtype)

    return df
