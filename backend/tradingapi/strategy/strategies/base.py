"""
策略基类和注册机制
"""

from abc import abstractmethod
from typing import Dict, Generic, List, Optional, Type, TypeVar

import pandas as pd
from loguru import logger

from tradingapi.fetcher.interface import OHLCVExtendedSchema
from tradingapi.strategy.base import SignalResult, SignalType, StrategyConfig
from tradingapi.strategy.config import BaseConfig
from tradingapi.strategy.config_manager import ConfigManager
from tradingapi.strategy.exceptions import (
    ConfigurationError,
    StrategyError,
    StrategyNotFoundError,
)
from tradingapi.strategy.manager import IndicatorManager


class StrategyRegistry:
    """策略注册表"""

    _strategies: Dict[str, Type["StrategyBase"]] = {}

    @classmethod
    def register(cls, name: str, strategy_class: Type["StrategyBase"]):
        """注册策略类"""
        cls._strategies[name] = strategy_class

    @classmethod
    def get(cls, name: str) -> Type["StrategyBase"]:
        """获取策略类"""
        if name not in cls._strategies:
            raise StrategyNotFoundError(f"Strategy {name} not found")
        return cls._strategies[name]

    @classmethod
    def list_strategies(cls) -> List[str]:
        """列出所有注册的策略"""
        return list(cls._strategies.keys())


def register_strategy(name: str):
    """策略注册装饰器"""

    def decorator(cls):
        StrategyRegistry.register(name, cls)
        return cls

    return decorator


TStrategyConfig = TypeVar("TStrategyConfig", bound="BaseConfig")


class StrategyBase(Generic[TStrategyConfig]):
    """统一的策略基类"""

    def __init__(
        self,
        config: StrategyConfig,
        indicator_manager: IndicatorManager,
        config_manager: ConfigManager = None,
    ):
        self.config = config
        self.name = config.name
        self.indicator_manager = indicator_manager
        self.config_manager = config_manager
        self.strategy_config: Optional[TStrategyConfig] = None

        # 初始化策略配置
        self._init_strategy_config()

    def _init_strategy_config(self) -> None:
        """初始化策略配置对象"""
        if self.config_manager is None:
            # 如果没有配置管理器，使用默认配置
            self.strategy_config = self.get_default_config()
        else:
            try:
                # 从配置管理器获取策略配置
                default_config = self.config_manager.get_strategy_config(self.name)
                # 使用传入的参数更新默认配置
                self.strategy_config = default_config.from_dict(self.config.parameters)
                self.strategy_config.validate()
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to initialize strategy config for {self.name}: {e}"
                )
        # 更新通用配置，以便后续使用
        self.config.parameters = self.strategy_config.to_dict()

    def prepare_indicators(self, df: pd.DataFrame) -> None:
        """准备策略所需的指标，确保所有必需指标都存在"""
        missing_indicators = []

        # 获取策略依赖的指标配置
        indicator_configs = self.get_indicator_configs()

        for indicator_name in self.required_indicators():
            if indicator_name not in df.columns:
                try:
                    # 使用策略特定的指标配置（如果有）
                    if indicator_name in indicator_configs:
                        # 更新指标管理器中的配置
                        self.indicator_manager.update_config(
                            indicator_name, indicator_configs[indicator_name].to_dict()
                        )

                    result = self.indicator_manager.calculate_indicator(
                        indicator_name, df
                    )
                    for col in result.values.columns:
                        df[col] = result.values[col]
                except Exception as e:
                    missing_indicators.append(indicator_name)
                    logger.error(
                        f"Failed to calculate indicator {indicator_name}: {e}, config:{indicator_configs[indicator_name]}"
                    )

        if missing_indicators:
            raise StrategyError(f"Missing required indicators: {missing_indicators}")

    def generate_signals_with_confidence(self, df: pd.DataFrame) -> SignalResult:
        """生成信号并计算置信度"""
        signal_result = self.generate_signals(df)

        # 如果策略没有提供置信度，则计算一个默认的
        if signal_result.confidence is None:
            signal_result.confidence = self._calculate_default_confidence(
                df, signal_result.signals
            )

        return signal_result

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> SignalResult:
        """生成交易信号"""

    @classmethod
    def get_default_parameters(cls) -> TStrategyConfig:
        """返回策略的默认参数"""
        return BaseConfig()

    @classmethod
    def get_required_indicators(cls) -> List[str]:
        """返回策略所需的指标列表"""
        raise NotImplementedError

    def get_indicator_configs(self) -> Dict[str, BaseConfig]:
        """返回策略依赖的指标配置"""
        return {}

    def validate_parameters(self) -> bool:
        """验证策略参数"""
        try:
            self.strategy_config.validate()
            return True
        except Exception as e:
            logger.error(f"Invalid parameters for strategy {self.name}: {e}")
            return False

    @abstractmethod
    def _calculate_default_confidence(
        self, df: pd.DataFrame, signals: pd.Series
    ) -> pd.Series:
        """计算默认置信度"""


class TrendStrategy(StrategyBase[TStrategyConfig]):
    """趋势策略基类"""

    def _calculate_default_confidence(
        self, df: pd.DataFrame, signals: pd.Series
    ) -> pd.Series:
        """趋势策略默认置信度计算"""
        # 使用价格变化率作为置信度
        price_change = df[OHLCVExtendedSchema.close].pct_change().abs()
        confidence = price_change.clip(0, 1)  # 限制在0-1范围
        return confidence.fillna(0)


class MomentumStrategy(StrategyBase[TStrategyConfig]):
    """动量策略基类"""

    def _calculate_default_confidence(
        self, df: pd.DataFrame, signals: pd.Series
    ) -> pd.Series:
        """动量策略默认置信度计算"""
        # 使用指标极值作为置信度
        confidence = pd.Series(0.5, index=df.index)  # 默认中等置信度

        # 买入信号时，使用超卖程度作为置信度
        buy_signals = signals == SignalType.BUY.value
        if "RSI" in df.columns:
            confidence.loc[buy_signals] = (30 - df["RSI"].clip(0, 30)) / 30

        # 卖出信号时，使用超买程度作为置信度
        sell_signals = signals == SignalType.SELL.value
        if "RSI" in df.columns:
            confidence.loc[sell_signals] = (df["RSI"].clip(70, 100) - 70) / 30

        return confidence.clip(0, 1)


class MeanReversionStrategy(StrategyBase[TStrategyConfig]):
    """均值回归策略基类"""

    def _calculate_default_confidence(
        self, df: pd.DataFrame, signals: pd.Series
    ) -> pd.Series:
        """均值回归策略默认置信度计算"""
        # 使用Z分数的绝对值（偏离越远，置信度越高）
        if "Z_Score" in df.columns:
            z_score = df["Z_Score"]
            confidence = (z_score.abs() / 2.0).clip(0, 1)  # 假设阈值为2
        else:
            confidence = pd.Series(0.5, index=df.index)

        return confidence.fillna(0)
