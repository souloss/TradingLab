"""
趋势类指标, 如移动平均线(MA)和MACD
"""

import pandas as pd

from ..config import EMAConfig, MAConfig
from .base import (IndicatorCalculator, IndicatorCategory, IndicatorResult,
                   register_indicator)


@register_indicator("MA")
class MovingAverage(IndicatorCalculator[MAConfig]):
    """移动平均线计算器"""

    @property
    def name(self) -> str:
        return "MA"

    @property
    def category(self) -> IndicatorCategory:
        return IndicatorCategory.TREND

    def calculate(self, df: pd.DataFrame, config: MAConfig) -> IndicatorResult:
        """计算移动平均线"""
        if not self.validate_inputs(df):
            raise ValueError("Invalid input data for MA calculation")

        close_prices = df["收盘"]

        # 计算各期移动平均线
        result_dict = {}
        for period in config.periods:
            result_dict[f"MA{period}"] = close_prices.rolling(window=period).mean()

        result_df = pd.DataFrame(result_dict, index=df.index)

        return IndicatorResult(
            name=self.name, values=result_df, metadata=config.to_dict()
        )


@register_indicator("EMA")
class ExponentialMovingAverage(IndicatorCalculator[EMAConfig]):
    """指数移动平均线计算器"""

    @property
    def name(self) -> str:
        return "EMA"

    @property
    def category(self) -> IndicatorCategory:
        return IndicatorCategory.TREND

    def calculate(self, df: pd.DataFrame, config: EMAConfig) -> IndicatorResult:
        """计算指数移动平均线"""
        if not self.validate_inputs(df):
            raise ValueError("Invalid input data for EMA calculation")

        close_prices = df["收盘"]

        # 计算各期指数移动平均线
        result_dict = {}
        for period in config.periods:
            result_dict[f"EMA{period}"] = close_prices.ewm(
                span=period, adjust=False
            ).mean()

        result_df = pd.DataFrame(result_dict, index=df.index)

        return IndicatorResult(
            name=self.name, values=result_df, metadata=config.to_dict()
        )
