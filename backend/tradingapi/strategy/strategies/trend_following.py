"""
趋势跟踪类策略，如均线交叉
"""

from typing import Dict, List

import pandas as pd

from tradingapi.fetcher.interface import OHLCVExtendedSchema
from tradingapi.strategy.base import SignalResult, SignalType
from tradingapi.strategy.config import (
    ATRBreakoutStrategyConfig,
    MACDStrategyConfig,
    MACrossStrategyConfig,
)
from tradingapi.strategy.config.base import BaseConfig
from tradingapi.strategy.strategies.base import TrendStrategy, register_strategy


@register_strategy("MA")
class MACrossStrategy(TrendStrategy[MACrossStrategyConfig]):
    """均线交叉策略"""

    @classmethod
    def get_default_config(self) -> BaseConfig:
        """返回策略的默认配置"""
        return MACrossStrategyConfig()

    @classmethod
    def required_indicators(self) -> List[str]:
        return ["MA"]

    def generate_signals(self, df: pd.DataFrame) -> SignalResult:
        """生成均线交叉信号"""
        # 获取策略配置
        config = self.strategy_config  # 类型: MACrossStrategyConfig

        # 获取均线周期
        fast_period = config.ma_config.periods[0]
        slow_period = config.ma_config.periods[1]

        fast_ma = f"MA{fast_period}"
        slow_ma = f"MA{slow_period}"

        # 初始化信号序列
        signals = pd.Series(SignalType.NEUTRAL.value, index=df.index)

        # 计算均线差值
        ma_diff = df[fast_ma] / df[slow_ma] - 1

        # 金叉信号（短期均线上穿长期均线）
        golden_cross = (ma_diff > config.signal_threshold) & (
            ma_diff.shift(1) <= config.signal_threshold
        )

        # 死叉信号（短期均线下穿长期均线）
        death_cross = (ma_diff < -config.signal_threshold) & (
            ma_diff.shift(1) >= -config.signal_threshold
        )

        # 设置信号
        signals.loc[golden_cross] = SignalType.BUY.value
        signals.loc[death_cross] = SignalType.SELL.value

        return SignalResult(
            strategy_name=self.name,
            signals=signals,
            metadata={
                "fast_period": fast_period,
                "slow_period": slow_period,
                "signal_threshold": config.signal_threshold,
            },
        )

    def get_indicator_configs(self) -> Dict[str, BaseConfig]:
        """返回策略依赖的指标配置"""
        return {"MA": self.strategy_config.ma_config}


@register_strategy("MACD")
class MACDStrategy(TrendStrategy[MACDStrategyConfig]):
    """MACD策略"""

    @classmethod
    def get_default_config(self) -> BaseConfig:
        """返回策略的默认配置"""
        return MACDStrategyConfig()

    @classmethod
    def required_indicators(self) -> List[str]:
        return ["MACD"]

    def generate_signals(self, df: pd.DataFrame) -> SignalResult:
        # 初始化信号序列
        signals = pd.Series(SignalType.NEUTRAL.value, index=df.index)

        # 获取策略配置
        config = self.strategy_config  # 类型: MACDStrategyConfig

        # MACD金叉（买入信号）
        macd_bullish = (df["MACD"] > df["MACD_Signal"]) & (
            df["MACD"].shift(1) <= df["MACD_Signal"].shift(1)
        )

        # MACD死叉（卖出信号）
        macd_bearish = (df["MACD"] < df["MACD_Signal"]) & (
            df["MACD"].shift(1) >= df["MACD_Signal"].shift(1)
        )

        # 柱状图由负转正（买入信号）
        histogram_bullish = (df["MACD_Hist"] > config.histogram_threshold) & (
            df["MACD_Hist"].shift(1) <= 0
        )

        # 柱状图由正转负（卖出信号）
        histogram_bearish = (df["MACD_Hist"] < -config.histogram_threshold) & (
            df["MACD_Hist"].shift(1) >= 0
        )

        # 综合信号
        buy_signals = macd_bullish | histogram_bullish
        sell_signals = macd_bearish | histogram_bearish

        # 设置信号
        signals.loc[buy_signals] = SignalType.BUY.value
        signals.loc[sell_signals] = SignalType.SELL.value

        # 计算置信度（基于MACD柱状图大小）
        confidence = df["MACD_Hist"].abs() / (df["MACD"].abs() + 1e-8)  # 避免除零
        confidence = confidence.clip(0, 1)

        return SignalResult(
            strategy_name=self.name,
            signals=signals,
            confidence=confidence,
            metadata={
                "histogram_threshold": config.histogram_threshold,
                "signal_line_threshold": config.signal_line_threshold,
            },
        )

    def get_indicator_configs(self) -> Dict[str, BaseConfig]:
        """返回策略依赖的指标配置"""
        return {"MACD": self.strategy_config.macd_config}


@register_strategy("ATR")
class ATRBreakoutStrategy(TrendStrategy[ATRBreakoutStrategyConfig]):
    """ATR突破策略"""

    @classmethod
    def get_default_config(self) -> BaseConfig:
        """返回策略的默认配置"""
        return ATRBreakoutStrategyConfig()

    @classmethod
    def required_indicators(self) -> List[str]:
        return ["ATR"]

    def generate_signals(self, df: pd.DataFrame) -> SignalResult:
        # 初始化信号序列
        signals = pd.Series(SignalType.NEUTRAL.value, index=df.index)

        # 获取策略配置
        config = self.strategy_config

        # 计算均值（使用简单移动平均）
        mean = (
            df[OHLCVExtendedSchema.close].rolling(window=config.breakout_period).mean()
        )

        # 计算上下轨
        upper_band = mean + df["ATR"] * config.atr_multiplier
        lower_band = mean - df["ATR"] * config.atr_multiplier

        # 生成买入信号（价格低于下轨，预期回归均值）
        buy_signals = df[OHLCVExtendedSchema.close] < lower_band

        # 生成卖出信号（价格高于上轨，预期回归均值）
        sell_signals = df[OHLCVExtendedSchema.close] > upper_band

        # 设置信号
        signals.loc[buy_signals] = SignalType.BUY.value
        signals.loc[sell_signals] = SignalType.SELL.value

        # 计算置信度（基于偏离程度）
        buy_deviation = (lower_band - df[OHLCVExtendedSchema.close]) / (
            df["ATR"] * config.atr_multiplier
        )
        sell_deviation = (df[OHLCVExtendedSchema.close] - upper_band) / (
            df["ATR"] * config.atr_multiplier
        )

        confidence = pd.Series(0.0, index=df.index)
        confidence.loc[buy_signals] = buy_deviation.loc[buy_signals].clip(0, 1)
        confidence.loc[sell_signals] = sell_deviation.loc[sell_signals].clip(0, 1)

        # # 添加趋势过滤（可选）
        # if config.trend_filter:
        #     # 使用长期均线判断趋势方向
        #     trend = df[OHLCVExtendedSchema.close].rolling(window=config.trend_period).mean()
        #     # 在下降趋势中只允许买入信号
        #     signals.loc[(signals == SignalType.SELL.value) & (df[OHLCVExtendedSchema.close] < trend)] = SignalType.NEUTRAL.value
        #     # 在上升趋势中只允许卖出信号
        #     signals.loc[(signals == SignalType.BUY.value) & (df[OHLCVExtendedSchema.close] > trend)] = SignalType.NEUTRAL.value

        return SignalResult(
            strategy_name=self.name,
            signals=signals,
            confidence=confidence,
            metadata={
                "breakout_period": config.breakout_period,
                "atr_multiplier": config.atr_multiplier,
            },
        )

    def get_indicator_configs(self) -> Dict[str, BaseConfig]:
        """返回策略依赖的指标配置"""
        return {"ATR": self.strategy_config.atr_config}
