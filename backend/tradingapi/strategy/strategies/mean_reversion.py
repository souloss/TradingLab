"""
均值回归策略
"""

from typing import Any, Dict, List

import pandas as pd
from loguru import logger

from tradingapi.fetcher.interface import OHLCVExtendedSchema
from tradingapi.strategy.config.base import BaseConfig

from tradingapi.strategy.base import SignalResult, SignalType
from tradingapi.strategy.config import BollingerBandsStrategyConfig
from tradingapi.strategy.strategies.base import MeanReversionStrategy, register_strategy


@register_strategy("BollingerBands")
class BollingerBandsStrategy(MeanReversionStrategy[BollingerBandsStrategyConfig]):
    """布林带策略"""

    @classmethod
    def get_default_config(self) -> BollingerBandsStrategyConfig:
        """返回策略的默认配置"""
        return BollingerBandsStrategyConfig()

    @classmethod
    def required_indicators(self) -> List[str]:
        return ["BollingerBands"]

    def generate_signals(self, df: pd.DataFrame) -> SignalResult:
        # 初始化信号序列
        signals = pd.Series(SignalType.NEUTRAL.value, index=df.index)
        # 获取策略配置
        config = self.strategy_config  # 类型: BollingerBandsStrategyConfig

        # 计算Z分数（价格相对于布林带的位置）
        bb_width = df["BB_Upper"] - df["BB_Lower"]
        z_score = (df[OHLCVExtendedSchema.close] - df["BB_Middle"]) / (bb_width / 2)

        # 生成信号
        buy_signal = z_score < -config.entry_threshold
        sell_signal = z_score > config.entry_threshold

        # 退出信号：价格回归中轨
        exit_buy = (z_score > -config.exit_threshold) & (
            signals.shift(1) == SignalType.BUY.value
        )
        exit_sell = (z_score < config.exit_threshold) & (
            signals.shift(1) == SignalType.SELL.value
        )

        # 设置信号
        signals.loc[buy_signal] = SignalType.BUY.value
        signals.loc[sell_signal] = SignalType.SELL.value
        signals.loc[exit_buy | exit_sell] = SignalType.NEUTRAL.value

        # 添加Z分数到元数据
        metadata = {
            "period": config.bb_config.period,
            "std_dev": config.bb_config.std_dev,
            "entry_threshold": config.entry_threshold,
            "exit_threshold": config.exit_threshold,
        }

        return SignalResult(strategy_name=self.name, signals=signals, metadata=metadata)

    def get_indicator_configs(self) -> Dict[str, BaseConfig]:
        """返回策略依赖的指标配置"""
        return {"BollingerBands": self.strategy_config.bb_config}
