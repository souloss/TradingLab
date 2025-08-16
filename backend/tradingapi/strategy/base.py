"""
策略系统基础定义
包含枚举、数据结构、抽象类等
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, TypeVar

import pandas as pd


# ==================== 基础类型和枚举 ====================
class SignalType(Enum):
    """交易信号类型"""

    BUY = 1  # 买入信号
    SELL = -1  # 卖出信号
    NEUTRAL = 0  # 中性信号（观望）


class MarketRegime(Enum):
    """市场状态枚举"""

    TRENDING_UP = auto()  # 上升趋势
    TRENDING_DOWN = auto()  # 下降趋势
    RANGING = auto()  # 震荡市场
    VOLATILE = auto()  # 高波动


class IndicatorCategory(Enum):
    """指标类别"""

    TREND = auto()  # 趋势类指标
    MOMENTUM = auto()  # 动量类指标
    VOLATILITY = auto()  # 波动率类指标
    VOLUME = auto()  # 成交量类指标


# ==================== 数据结构 ====================
@dataclass
class IndicatorResult:
    """技术指标计算结果"""

    name: str
    values: pd.DataFrame
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_column(self, column_name: str) -> pd.Series:
        """获取指定列的数据"""
        if column_name in self.values.columns:
            return self.values[column_name]
        raise ValueError(f"Column {column_name} not found in indicator {self.name}")


@dataclass
class SignalResult:
    """策略信号结果"""

    strategy_name: str
    signals: pd.Series
    confidence: Optional[pd.Series] = None  # 信号置信度 (0-1)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_buy_signals(self) -> pd.Series:
        """获取买入信号"""
        return self.signals[self.signals == SignalType.BUY.value]

    def get_sell_signals(self) -> pd.Series:
        """获取卖出信号"""
        return self.signals[self.signals == SignalType.SELL.value]


@dataclass
class StrategyConfig:
    """策略配置"""

    name: str
    enabled: bool = True
    weight: float = 1.0
    parameters: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "StrategyConfig":
        """从字典创建策略配置"""
        # 提取已知字段
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_config = {k: v for k, v in config_dict.items() if k in known_fields}

        return cls(**filtered_config)

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """获取参数值"""
        return self.parameters.get(key, default)

    def set_parameter(self, key: str, value: Any) -> None:
        """设置参数值"""
        self.parameters[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "weight": self.weight,
            "parameters": self.parameters,
        }
