"""
Strategy包初始化文件
导出主要类和函数
"""

from .base import (IndicatorResult, MarketRegime, SignalResult, SignalType,
                   StrategyConfig)
from .config import (ATRConfig, BollingerBandsConfig, MACDConfig, MAConfig,
                     RSIConfig, VolumeConfig)
from .config_manager import ConfigManager
from .exceptions import (ConfigurationError, IndicatorError,
                         IndicatorNotFoundError, StrategyError,
                         StrategyNotFoundError)
from .manager import SignalManager, SignalManagerConfig, create_signal_manager

# 导出主要类和函数
__all__ = [
    # 基础类型
    "SignalType",
    "MarketRegime",
    "IndicatorResult",
    "SignalResult",
    "StrategyConfig",
    # 配置类
    "ConfigManager",
    "MAConfig",
    "MACDConfig",
    "RSIConfig",
    "ATRConfig",
    "BollingerBandsConfig",
    "VolumeConfig",
    # 管理器
    "SignalManager",
    "SignalManagerConfig",
    "create_signal_manager",
    # 异常类
    "StrategyError",
    "StrategyNotFoundError",
    "IndicatorError",
    "IndicatorNotFoundError",
    "ConfigurationError",
]
