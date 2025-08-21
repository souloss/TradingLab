"""
动量类指标 (RSI, KDJ)
"""

import pandas as pd

from tradingapi.fetcher.interface import OHLCVExtendedSchema
from tradingapi.strategy.config import KDJConfig, MACDConfig, RSIConfig

from tradingapi.strategy.base import IndicatorCategory, IndicatorResult
from tradingapi.strategy.indicators.base import IndicatorCalculator, register_indicator


@register_indicator("RSI")
class RSICalculator(IndicatorCalculator[RSIConfig]):
    @property
    def name(self) -> str:
        return "RSI"

    @property
    def category(self) -> IndicatorCategory:
        return IndicatorCategory.MOMENTUM

    def calculate(self, df: pd.DataFrame, config: RSIConfig) -> IndicatorResult:
        delta = df[OHLCVExtendedSchema.close].diff()
        gain = delta.where(delta > 0, 0).rolling(window=config.period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=config.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        result_df = pd.DataFrame({"RSI": rsi}, index=df.index)

        return IndicatorResult(
            name=self.name, values=result_df, metadata=config.to_dict()
        )


@register_indicator("KDJ")
class KDJCalculator(IndicatorCalculator[KDJConfig]):
    @property
    def name(self) -> str:
        return "KDJ"

    @property
    def category(self) -> IndicatorCategory:
        return IndicatorCategory.MOMENTUM

    def calculate(self, df: pd.DataFrame, config: KDJConfig) -> IndicatorResult:
        low_list = df[OHLCVExtendedSchema.low].rolling(window=config.period).min()
        high_list = df[OHLCVExtendedSchema.high].rolling(window=config.period).max()
        rsv = (df[OHLCVExtendedSchema.close] - low_list) / (high_list - low_list) * 100

        k = rsv.ewm(com=config.slow - 1, adjust=False).mean()
        d = k.ewm(com=config.signal - 1, adjust=False).mean()
        j = 3 * k - 2 * d

        result_df = pd.DataFrame({"K": k, "D": d, "J": j}, index=df.index)

        return IndicatorResult(
            name=self.name, values=result_df, metadata=config.to_dict()
        )


@register_indicator("MACD")
class MACD(IndicatorCalculator[MACDConfig]):
    """MACD指标计算器"""

    @property
    def name(self) -> str:
        return "MACD"

    @property
    def category(self) -> IndicatorCategory:
        return IndicatorCategory.MOMENTUM

    def calculate(self, df: pd.DataFrame, config: MACDConfig) -> IndicatorResult:
        """计算MACD指标"""
        if not self.validate_inputs(df):
            raise ValueError("Invalid input data for MACD calculation")

        close_prices = df[OHLCVExtendedSchema.close]

        # 计算快慢EMA
        ema_fast = close_prices.ewm(span=config.fast_period, adjust=False).mean()
        ema_slow = close_prices.ewm(span=config.slow_period, adjust=False).mean()

        # 计算MACD线
        macd_line = ema_fast - ema_slow
        # 计算信号线
        signal_line = macd_line.ewm(span=config.signal_period, adjust=False).mean()
        # 计算柱状图
        histogram = macd_line - signal_line

        result_df = pd.DataFrame(
            {"MACD": macd_line, "MACD_Signal": signal_line, "MACD_Hist": histogram},
            index=df.index,
        )

        return IndicatorResult(
            name=self.name, values=result_df, metadata=config.to_dict()
        )
