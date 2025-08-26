"""
配置管理模块
统一管理指标配置和策略配置
"""

from typing import Any, Dict

from .config import (
    ATRBreakoutStrategyConfig,
    ATRConfig,
    BaseConfig,
    BollingerBandsConfig,
    BollingerBandsStrategyConfig,
    EMAConfig,
    KDJConfig,
    MACDConfig,
    MACDStrategyConfig,
    MAConfig,
    MACrossStrategyConfig,
    RSIConfig,
    RSIStrategyConfig,
    VolumeConfig,
    VolumeSpikeStrategyConfig,
)
from .exceptions import ConfigurationError


class ConfigManager:
    """统一的配置管理器"""

    def __init__(self):
        # 指标配置
        self.indicator_configs: Dict[str, BaseConfig] = {
            "MA": MAConfig(),
            "EMA": EMAConfig(),
            "MACD": MACDConfig(),
            "KDJ": KDJConfig(),
            "RSI": RSIConfig(),
            "ATR": ATRConfig(),
            "BollingerBands": BollingerBandsConfig(),
            "VOLUME": VolumeConfig(),
        }

        # 策略配置
        self.strategy_configs: Dict[str, BaseConfig] = {
            "RSI": RSIStrategyConfig(),
            "VOLUME": VolumeSpikeStrategyConfig(),
            "MA": MACrossStrategyConfig(),
            "MACD": MACDStrategyConfig(),
            "ATR": ATRBreakoutStrategyConfig(),
            "BollingerBands": BollingerBandsStrategyConfig(),
        }

    def get_indicator_config(self, indicator_name: str) -> BaseConfig:
        """获取指标配置"""
        if indicator_name not in self.indicator_configs:
            raise ConfigurationError(f"Unknown indicator: {indicator_name}")
        return self.indicator_configs[indicator_name]

    def get_strategy_config(self, strategy_name: str) -> BaseConfig:
        """获取策略配置"""
        if strategy_name not in self.strategy_configs:
            raise ConfigurationError(f"Unknown strategy: {strategy_name}")
        return self.strategy_configs[strategy_name]

    def update_indicator_config(
        self, indicator_name: str, config: Dict[str, Any]
    ) -> None:
        """更新指标配置"""
        if indicator_name not in self.indicator_configs:
            raise ConfigurationError(f"Unknown indicator: {indicator_name}")

        config_class = type(self.indicator_configs[indicator_name])
        new_config = config_class.from_dict(config)
        new_config.validate()  # 验证新配置
        self.indicator_configs[indicator_name] = new_config

    def update_strategy_config(
        self, strategy_name: str, config: Dict[str, Any]
    ) -> None:
        """更新策略配置"""
        if strategy_name not in self.strategy_configs:
            raise ConfigurationError(f"Unknown strategy: {strategy_name}")

        config_class = type(self.strategy_configs[strategy_name])
        new_config = config_class.from_dict(config)
        new_config.validate()  # 验证新配置
        self.strategy_configs[strategy_name] = new_config

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "indicators": {
                name: config.to_dict()
                for name, config in self.indicator_configs.items()
            },
            "strategies": {
                name: config.to_dict() for name, config in self.strategy_configs.items()
            },
        }

    def from_dict(self, config_dict: Dict[str, Any]) -> None:
        """从字典加载配置"""
        if "indicators" in config_dict:
            for name, config in config_dict["indicators"].items():
                self.update_indicator_config(name, config)

        if "strategies" in config_dict:
            for name, config in config_dict["strategies"].items():
                self.update_strategy_config(name, config)
