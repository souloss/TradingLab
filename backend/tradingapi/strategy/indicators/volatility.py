"""
波动率类指标
"""

import numpy as np
import pandas as pd

from ..base import IndicatorCategory, IndicatorResult
from ..config import ATRConfig, BollingerBandsConfig, VolumeConfig
from .base import IndicatorCalculator, register_indicator


@register_indicator("ATR")
class AverageTrueRange(IndicatorCalculator[ATRConfig]):
    """ATR指标计算器"""

    @property
    def name(self) -> str:
        return "ATR"

    @property
    def category(self) -> IndicatorCategory:
        return IndicatorCategory.VOLATILITY

    def calculate(self, df: pd.DataFrame, config: ATRConfig) -> IndicatorResult:
        """计算ATR指标"""
        if not self.validate_inputs(df):
            raise ValueError("Invalid input data for ATR calculation")

        high = df["最高"]
        low = df["最低"]
        close = df["收盘"]

        # 计算真实波幅
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        tr = np.maximum(tr1, np.maximum(tr2, tr3))

        # 计算ATR
        atr = tr.rolling(window=config.period).mean()

        result_df = pd.DataFrame({"ATR": atr}, index=df.index)

        return IndicatorResult(
            name=self.name, values=result_df, metadata=config.to_dict()
        )


@register_indicator("BollingerBands")
class BollingerBands(IndicatorCalculator[BollingerBandsConfig]):
    """布林带指标计算器"""

    @property
    def name(self) -> str:
        return "BollingerBands"

    @property
    def category(self) -> IndicatorCategory:
        return IndicatorCategory.VOLATILITY

    def calculate(
        self, df: pd.DataFrame, config: BollingerBandsConfig
    ) -> IndicatorResult:
        """计算布林带指标"""
        if not self.validate_inputs(df):
            raise ValueError("Invalid input data for Bollinger Bands calculation")

        close = df["收盘"]

        # 计算中轨（简单移动平均线）
        middle = close.rolling(window=config.period).mean()

        # 计算标准差
        std = close.rolling(window=config.period).std()

        # 计算上轨和下轨
        upper = middle + (std * config.std_dev)
        lower = middle - (std * config.std_dev)

        result_df = pd.DataFrame(
            {"BB_Upper": upper, "BB_Middle": middle, "BB_Lower": lower}, index=df.index
        )

        return IndicatorResult(
            name=self.name, values=result_df, metadata=config.to_dict()
        )
