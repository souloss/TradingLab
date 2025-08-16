"""
动量类策略
"""

from typing import Dict, List

import pandas as pd
from loguru import logger

from tradingapi.strategy.config.base import BaseConfig

from ..base import SignalResult, SignalType
from ..config import RSIStrategyConfig, VolumeSpikeStrategyConfig
from .base import MomentumStrategy, register_strategy


@register_strategy("RSI")
class RSIStrategy(MomentumStrategy[RSIStrategyConfig]):
    """RSI策略"""

    @classmethod
    def get_default_config(self) -> BaseConfig:
        """返回策略的默认配置"""
        return RSIStrategyConfig()

    @classmethod
    def required_indicators(self) -> List[str]:
        return ["RSI"]

    def generate_signals(self, df: pd.DataFrame) -> SignalResult:
        # 初始化信号序列
        signals = pd.Series(SignalType.NEUTRAL.value, index=df.index)

        # 直接使用所需指标，不再检查存在性
        # 获取策略配置
        config = self.strategy_config  # 类型: RSIStrategyConfig

        # 超卖信号（买入）
        oversold = df["RSI"] < config.oversold_threshold

        # 超买信号（卖出）
        overbought = df["RSI"] > config.overbought_threshold

        # RSI从超卖区域回升（确认买入信号）
        recovery_from_oversold = oversold & (
            df["RSI"].rolling(window=config.lookback_period).min()
            > config.oversold_threshold
        )

        # RSI从超买区域回落（确认卖出信号）
        pullback_from_overbought = overbought & (
            df["RSI"].rolling(window=config.lookback_period).max()
            < config.overbought_threshold
        )

        # 设置信号
        signals.loc[recovery_from_oversold] = SignalType.BUY.value
        signals.loc[pullback_from_overbought] = SignalType.SELL.value

        return SignalResult(
            strategy_name=self.name,
            signals=signals,
            metadata={
                "oversold_threshold": config.oversold_threshold,
                "overbought_threshold": config.overbought_threshold,
                "lookback_period": config.lookback_period,
            },
        )

    def get_indicator_configs(self) -> Dict[str, BaseConfig]:
        """返回策略依赖的指标配置"""
        return {"RSI": self.strategy_config.rsi_config}


@register_strategy("VOLUME")
class VolumeSpikeStrategy(MomentumStrategy[VolumeSpikeStrategyConfig]):
    """量能异动策略"""

    @classmethod
    def get_default_config(self) -> BaseConfig:
        """返回策略的默认配置"""
        return VolumeSpikeStrategyConfig()

    def generate_signals(self, df: pd.DataFrame) -> SignalResult:
        # 初始化信号序列
        signals = pd.Series(SignalType.NEUTRAL.value, index=df.index)

        # 获取策略配置
        config = self.strategy_config  # 类型: VolumeSpikeStrategyConfig

        # 计算成交量均线
        vol_ma_col = f"Vol_MA{config.period}"

        # 量能放大（天量）
        volume_spike = df["成交量"] > df[vol_ma_col] * config.high_multiplier

        # 量能萎缩（地量）
        volume_dip = df["成交量"] < df[vol_ma_col] * config.high_multiplier

        # 计算价格位置（用于确认）

        price_min = (
            df["收盘"].rolling(window=config.period, min_periods=config.period).min()
        )
        price_max = (
            df["收盘"].rolling(window=config.period, min_periods=config.period).max()
        )

        # 地量地价买入信号
        buy_signal = volume_dip & price_min * 0.95

        # 天量天价卖出信号
        sell_signal = volume_spike & price_max * 1.05

        # 设置信号
        signals.loc[buy_signal] = SignalType.BUY.value
        signals.loc[sell_signal] = SignalType.SELL.value

        return SignalResult(
            strategy_name=self.name,
            signals=signals,
            metadata={
                "period": config.period,
                "high_multiplier": config.high_multiplier,
                "low_multiplier": config.low_multiplier,
            },
        )

    @classmethod
    def required_indicators(self) -> List[str]:
        return ["VOLUME"]

    def get_indicator_configs(self) -> Dict[str, BaseConfig]:
        """返回策略依赖的指标配置"""
        return {"Volume": self.strategy_config.volume_config}
