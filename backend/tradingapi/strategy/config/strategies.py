"""
策略配置类定义
包含所有交易策略的配置参数
"""

from dataclasses import dataclass, field

from .base import BaseConfig
from .indicators import (ATRConfig, BollingerBandsConfig, MACDConfig, MAConfig,
                         RSIConfig, VolumeConfig)


@dataclass
class RSIStrategyConfig(BaseConfig):
    """RSI策略配置"""

    # 策略特有参数
    oversold_threshold: float = 30
    overbought_threshold: float = 70
    lookback_period: int = 5

    # 依赖的指标配置
    rsi_config: RSIConfig = field(default_factory=RSIConfig)

    def validate(self) -> None:
        if not isinstance(self.oversold_threshold, (int, float)):
            raise ValueError("oversold_threshold must be a number")
        if not isinstance(self.overbought_threshold, (int, float)):
            raise ValueError("overbought_threshold must be a number")
        if not isinstance(self.lookback_period, int) or self.lookback_period <= 0:
            raise ValueError("lookback_period must be a positive integer")
        if self.oversold_threshold >= self.overbought_threshold:
            raise ValueError(
                "oversold_threshold must be less than overbought_threshold"
            )
        if self.oversold_threshold < 0 or self.oversold_threshold > 100:
            raise ValueError("oversold_threshold must be between 0 and 100")
        if self.overbought_threshold < 0 or self.overbought_threshold > 100:
            raise ValueError("overbought_threshold must be between 0 and 100")
        # 验证依赖的指标配置
        self.rsi_config.validate()


@dataclass
class VolumeSpikeStrategyConfig(BaseConfig):
    """量能异动策略配置"""

    # 策略特有参数
    period: int = 20
    high_multiplier: float = 2.0
    low_multiplier: float = 0.6

    # 依赖的指标配置
    volume_config: VolumeConfig = field(default_factory=VolumeConfig)

    def validate(self) -> None:
        if not isinstance(self.period, int) or self.period <= 0:
            raise ValueError("period must be a positive integer")
        if (
            not isinstance(self.high_multiplier, (int, float))
            or self.high_multiplier <= 0
        ):
            raise ValueError("high_multiplier must be a positive number")
        if (
            not isinstance(self.low_multiplier, (int, float))
            or self.low_multiplier <= 0
        ):
            raise ValueError("low_multiplier must be a positive number")
        if self.low_multiplier >= 1.0:
            raise ValueError("low_multiplier must be less than 1.0")
        # 验证依赖的指标配置
        self.volume_config.validate()


@dataclass
class MACrossStrategyConfig(BaseConfig):
    """均线交叉策略配置"""

    # 策略特有参数
    signal_threshold: float = 0.01

    # 依赖的指标配置
    ma_config: MAConfig = field(default_factory=MAConfig)

    def validate(self) -> None:
        if (
            not isinstance(self.signal_threshold, (int, float))
            or self.signal_threshold <= 0
        ):
            raise ValueError("signal_threshold must be a positive number")
        # 验证依赖的指标配置
        self.ma_config.validate()
        if len(self.ma_config.periods) < 2:
            raise ValueError("MA strategy requires at least 2 periods")


@dataclass
class MACDStrategyConfig(BaseConfig):
    """MACD策略配置"""

    # 策略特有参数
    histogram_threshold: float = 0.1
    signal_line_threshold: float = 0.05

    # 依赖的指标配置
    macd_config: MACDConfig = field(default_factory=MACDConfig)

    def validate(self) -> None:
        if (
            not isinstance(self.histogram_threshold, (int, float))
            or self.histogram_threshold < 0
        ):
            raise ValueError("histogram_threshold must be a non-negative number")
        if (
            not isinstance(self.signal_line_threshold, (int, float))
            or self.signal_line_threshold < 0
        ):
            raise ValueError("signal_line_threshold must be a non-negative number")
        # 验证依赖的指标配置
        self.macd_config.validate()


@dataclass
class ATRBreakoutStrategyConfig(BaseConfig):
    """ATR突破策略配置"""

    # 策略特有参数
    breakout_period: int = 20
    atr_multiplier: float = 1.5

    # 依赖的指标配置
    atr_config: ATRConfig = field(default_factory=ATRConfig)

    def validate(self) -> None:
        if not isinstance(self.breakout_period, int) or self.breakout_period <= 0:
            raise ValueError("breakout_period must be a positive integer")
        if (
            not isinstance(self.atr_multiplier, (int, float))
            or self.atr_multiplier <= 0
        ):
            raise ValueError("atr_multiplier must be a positive number")
        # 验证依赖的指标配置
        self.atr_config.validate()


@dataclass
class BollingerBandsStrategyConfig(BaseConfig):
    """布林带策略配置"""

    # 策略特有参数
    entry_threshold: float = 0.8  # 进入信号阈值（0-1）
    exit_threshold: float = 0.5  # 退出信号阈值（0-1）

    # 依赖的指标配置
    bb_config: BollingerBandsConfig = field(default_factory=BollingerBandsConfig)

    def validate(self) -> None:
        if not isinstance(self.entry_threshold, (int, float)) or not (
            0 < self.entry_threshold <= 1
        ):
            raise ValueError("entry_threshold must be between 0 and 1")
        if not isinstance(self.exit_threshold, (int, float)) or not (
            0 < self.exit_threshold <= 1
        ):
            raise ValueError("exit_threshold must be between 0 and 1")
        if self.exit_threshold >= self.entry_threshold:
            raise ValueError("exit_threshold must be less than entry_threshold")
        # 验证依赖的指标配置
        self.bb_config.validate()
