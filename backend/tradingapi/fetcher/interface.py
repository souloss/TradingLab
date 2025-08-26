from typing import Protocol

import pandas as pd
import pandera.pandas as pa
from pandera.typing import DataFrame, Index, Series

from tradingapi.models.stock_basic_info import StockBasicInfo


class OHLCVSchema(pa.DataFrameModel):
    # 时间戳索引（主键）
    timestamp: Index[pa.DateTime] = pa.Field(
        unique=True, coerce=True, description="时间索引"
    )

    # 价格列（需为正浮点数）
    open: Series[pa.Float] = pa.Field(gt=0, description="开盘价")
    high: Series[pa.Float] = pa.Field(gt=0, description="最高价")
    low: Series[pa.Float] = pa.Field(gt=0, description="最低价")
    close: Series[pa.Float] = pa.Field(gt=0, description="收盘价")

    # 成交量列（非负整数）
    volume: Series[pa.Int] = pa.Field(ge=0, coerce=True, description="成交量")

    # 最高价校验：必须 ≥ 开盘价、收盘价、最低价
    @pa.dataframe_check
    def check_high(cls, df: DataFrame) -> Series[bool]:
        """向量化校验：high >= open/close/low"""
        return (
            (df[OHLCVSchema.high] >= df[OHLCVSchema.open])
            & (df[OHLCVSchema.high] >= df[OHLCVSchema.close])
            & (df[OHLCVSchema.high] >= df[OHLCVSchema.low])
        )

    # 最低价校验：必须 ≤ 开盘价、收盘价、最高价
    @pa.dataframe_check
    def check_low(cls, df: DataFrame) -> Series[bool]:
        """向量化校验：low <= open/close/high"""
        return (
            (df[OHLCVSchema.low] <= df[OHLCVSchema.open])
            & (df[OHLCVSchema.low] <= df[OHLCVSchema.close])
            & (df[OHLCVSchema.low] <= df[OHLCVSchema.high])
        )

    # 自定义验证：时间连续性（需在调用时传入 timeframe）
    @classmethod
    def check_time_continuity(cls, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        time_diff = df.index.to_series().diff().dropna()
        expected_diff = pd.Timedelta(timeframe)  # 如 '1h', '15min'
        invalid_gaps = time_diff[time_diff != expected_diff]
        if not invalid_gaps.empty:
            raise ValueError(f"时间序列不连续，发现{len(invalid_gaps)}个异常间隔")
        return df

    class Config:
        # 严格模式：禁止未定义的列
        # strict = True
        # 自动将索引名重置为 'timestamp'
        name = "timestamp"
        coerce = True  # 自动类型转换


class OHLCVExtendedSchema(OHLCVSchema):
    symbol: Series[pa.String] = pa.Field(description="股票代码")
    trading_value: Series[pa.Float] = pa.Field(description="成交额", nullable=True)
    amplitude: Series[pa.Float] = pa.Field(description="振幅", nullable=True)
    pct_change: Series[pa.Float] = pa.Field(description="涨跌幅", nullable=True)
    price_change: Series[pa.Float] = pa.Field(description="涨跌额", nullable=True)
    turnover_rate: Series[pa.Int] = pa.Field(description="换手率", nullable=True)

    class Config:
        # 严格模式：禁止未定义的列
        # strict = True
        # 自动将索引名重置为 'timestamp'
        name = "timestamp"
        coerce = True  # 自动类型转换


class StockInfoFetcher(Protocol):

    async def get_all_stock_basic_info(self): ...

    async def get_stock_basic_info(self, exchange, symbol): ...

    @pa.check_types
    async def fetch_stock_daily_data(
        self, stock: StockBasicInfo, start_date: str, end_date: str
    ) -> DataFrame[OHLCVExtendedSchema]:
        """
        获取股票日线数据的接口
        """
        ...


class StockIndustryFetcher(Protocol):
    async def fetch_industry_info(
        self,
    ) -> pd.DataFrame: ...
    async def fetch_single_third_cons(self, industry) -> list[dict]: ...
