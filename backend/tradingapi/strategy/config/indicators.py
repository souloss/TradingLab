"""
指标配置类定义
包含所有技术指标的配置参数
"""

from dataclasses import dataclass, field
from typing import List

from tradingapi.strategy.config.base import BaseConfig


@dataclass
class MAConfig(BaseConfig):
    """移动平均线配置"""

    periods: List[int] = field(default_factory=lambda: [5, 10, 20, 60, 120])

    def validate(self) -> None:
        if not isinstance(self.periods, list):
            raise ValueError("periods must be a list")
        if not all(isinstance(p, int) and p > 0 for p in self.periods):
            raise ValueError("All periods must be positive integers")
        if len(self.periods) != len(set(self.periods)):
            raise ValueError("Periods must be unique")


@dataclass
class EMAConfig(BaseConfig):
    """指数移动平均线配置"""

    periods: List[int] = field(default_factory=lambda: [5, 10, 20, 60, 120])

    def validate(self) -> None:
        if not isinstance(self.periods, list):
            raise ValueError("periods must be a list")
        if not all(isinstance(p, int) and p > 0 for p in self.periods):
            raise ValueError("All periods must be positive integers")
        if len(self.periods) != len(set(self.periods)):
            raise ValueError("Periods must be unique")


@dataclass
class MACDConfig(BaseConfig):
    """MACD配置"""

    fast_period: int = 12
    slow_period: int = 26
    signal_period: int = 9

    def validate(self) -> None:
        if not isinstance(self.fast_period, int) or self.fast_period <= 0:
            raise ValueError("fast_period must be a positive integer")
        if not isinstance(self.slow_period, int) or self.slow_period <= 0:
            raise ValueError("slow_period must be a positive integer")
        if not isinstance(self.signal_period, int) or self.signal_period <= 0:
            raise ValueError("signal_period must be a positive integer")
        if self.fast_period >= self.slow_period:
            raise ValueError("fast_period must be less than slow_period")


@dataclass
class KDJConfig(BaseConfig):
    """KDJ配置"""

    period: int = 9
    slow: int = 3
    signal: int = 3

    def validate(self) -> None:
        if not isinstance(self.period, int) or self.period <= 0:
            raise ValueError("period must be a positive integer")
        if not isinstance(self.slow, int) or self.slow <= 0:
            raise ValueError("slow must be a positive integer")
        if not isinstance(self.signal, int) or self.signal <= 0:
            raise ValueError("signal must be a positive integer")


@dataclass
class RSIConfig(BaseConfig):
    """RSI配置"""

    period: int = 14

    def validate(self) -> None:
        if not isinstance(self.period, int) or self.period <= 0:
            raise ValueError("period must be a positive integer")


@dataclass
class ATRConfig(BaseConfig):
    """ATR配置"""

    period: int = 14

    def validate(self) -> None:
        if not isinstance(self.period, int) or self.period <= 0:
            raise ValueError("period must be a positive integer")


@dataclass
class BollingerBandsConfig(BaseConfig):
    """布林带配置"""

    period: int = 20
    std_dev: float = 2.0

    def validate(self) -> None:
        if not isinstance(self.period, int) or self.period <= 0:
            raise ValueError("period must be a positive integer")
        if not isinstance(self.std_dev, (int, float)) or self.std_dev <= 0:
            raise ValueError("std_dev must be a positive number")


@dataclass
class VolumeConfig(BaseConfig):
    """成交量指标配置"""

    ma_periods: List[int] = field(default_factory=lambda: [5, 10, 20])

    def validate(self) -> None:
        if not isinstance(self.ma_periods, list):
            raise ValueError("ma_periods must be a list")
        if not all(isinstance(p, int) and p > 0 for p in self.ma_periods):
            raise ValueError("All ma_periods must be positive integers")
        if len(self.ma_periods) != len(set(self.ma_periods)):
            raise ValueError("ma_periods must be unique")
