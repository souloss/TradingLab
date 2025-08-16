"""
信号管理器
负责策略管理和信号生成
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd
from loguru import logger

from .base import SignalResult, SignalType, StrategyConfig
from .config_manager import ConfigManager
from .exceptions import ConfigurationError, StrategyNotFoundError
from .indicators.base import IndicatorManager
from .strategies.base import StrategyBase, StrategyRegistry


@dataclass
class SignalManagerConfig:
    """信号管理器配置"""

    indicator_configs: Dict[str, Any] = field(default_factory=dict)
    strategy_configs: List[Dict[str, Any]] = field(default_factory=list)


class SignalManager:
    """信号管理器 - 负责策略管理和信号生成"""

    def __init__(self, config: SignalManagerConfig = None):
        self.config = config or SignalManagerConfig()

        # 初始化配置管理器
        self.config_manager = ConfigManager()

        # 应用传入的指标配置
        if self.config.indicator_configs:
            for name, config_dict in self.config.indicator_configs.items():
                try:
                    self.config_manager.update_indicator_config(name, config_dict)
                except Exception as e:
                    logger.warning(f"Failed to update indicator config for {name}: {e}")

        # 初始化指标管理器
        self.indicator_manager = IndicatorManager(self.config_manager)

        # 策略字典
        self.strategies = {}
        self.strategy_configs = {}

        # 注册内置策略类
        self._register_builtin_strategies()

        # 添加传入的策略配置
        if self.config.strategy_configs:
            for strategy_config_dict in self.config.strategy_configs:
                try:
                    strategy_config = StrategyConfig.from_dict(strategy_config_dict)
                    self.add_strategy(strategy_config)
                except Exception as e:
                    logger.warning(
                        f"Failed to add strategy {strategy_config_dict.get('name', 'unknown')}: {e}"
                    )

    def _register_builtin_strategies(self):
        """注册内置策略类"""
        # 导入所有策略模块，这样装饰器会自动注册策略
        from .strategies import mean_reversion, momentum, trend_following

    def add_strategy(self, strategy_config: StrategyConfig):
        """添加策略"""
        strategy_class = StrategyRegistry.get(strategy_config.name)
        strategy = strategy_class(
            strategy_config, self.indicator_manager, self.config_manager
        )
        # 验证策略参数
        if not strategy.validate_parameters():
            raise ConfigurationError(
                f"Invalid parameters for strategy: {strategy_config.name}"
            )

        self.strategies[strategy_config.name] = strategy
        self.strategy_configs[strategy_config.name] = strategy_config
        logger.info(f"Added strategy: {strategy_config.name}")

    def remove_strategy(self, name: str) -> bool:
        """移除策略"""
        if name in self.strategies:
            del self.strategies[name]
            del self.strategy_configs[name]
            logger.info(f"Removed strategy: {name}")
            return True
        return False

    def enable_strategy(self, name: str, enabled: bool = True) -> bool:
        """启用/禁用策略"""
        if name in self.strategy_configs:
            self.strategy_configs[name].enabled = enabled
            logger.info(f"Strategy {name} {'enabled' if enabled else 'disabled'}")
            return True
        return False

    def set_strategy_weight(self, name: str, weight: float) -> bool:
        """设置策略权重"""
        if name in self.strategy_configs:
            self.strategy_configs[name].weight = max(0, min(weight, 10))  # 限制权重范围
            logger.info(f"Set strategy {name} weight to {weight}")
            return True
        return False

    def update_indicator_config(
        self, indicator_name: str, config: Dict[str, Any]
    ) -> None:
        """更新指标配置"""
        self.indicator_manager.update_config(indicator_name, config)
        logger.info(f"Updated indicator config for {indicator_name}")

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成所有策略的信号"""
        df = df.copy()
        # 为每个策略生成信号
        for name, strategy in self.strategies.items():
            if self.strategy_configs[name].enabled:
                try:
                    # 准备策略所需的指标
                    strategy.prepare_indicators(df)

                    # 生成信号
                    signal_result = strategy.generate_signals_with_confidence(df)

                    # 添加信号列
                    df[f"Signal_{name}"] = signal_result.signals

                    # 添加置信度列
                    if signal_result.confidence is not None:
                        df[f"Confidence_{name}"] = signal_result.confidence

                    # 添加元数据
                    for key, value in signal_result.metadata.items():
                        df[f"Meta_{name}_{key}"] = value

                except Exception as e:
                    logger.error(f"Failed to generate signals for strategy {name}: {e}")
                    # 添加中性信号
                    df[f"Signal_{name}"] = SignalType.NEUTRAL.value
                    df[f"Confidence_{name}"] = 0.0
            else:
                # 对于禁用的策略，直接添加中性信号
                df[f"Signal_{name}"] = SignalType.NEUTRAL.value
                df[f"Confidence_{name}"] = 0.0
                logger.debug(f"Strategy {name} is disabled, using neutral signals")
        # 计算综合信号
        self._calculate_combined_signal(df)

        return df

    def _calculate_combined_signal(self, df: pd.DataFrame) -> None:
        """计算综合信号"""
        # 获取所有启用的策略
        enabled_strategies = [
            name for name, config in self.strategy_configs.items() if config.enabled
        ]

        if not enabled_strategies:
            df["Signal_Combined"] = SignalType.NEUTRAL.value
            df["Signal_Confidence"] = 0.0
            return

        # 获取信号列
        signal_cols = [f"Signal_{name}" for name in enabled_strategies]
        confidence_cols = [
            f"Confidence_{name}"
            for name in enabled_strategies
            if f"Confidence_{name}" in df.columns
        ]

        # 计算权重
        weights = [self.strategy_configs[name].weight for name in enabled_strategies]

        # 归一化权重
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]

        # 计算加权信号
        weighted_signals = df[signal_cols].multiply(weights, axis=1)
        df["Signal_Combined"] = weighted_signals.sum(axis=1)

        # 计算加权置信度
        if confidence_cols:
            weighted_confidence = df[confidence_cols].multiply(weights, axis=1)
            df["Signal_Confidence"] = weighted_confidence.sum(axis=1)
        else:
            df["Signal_Confidence"] = 1.0

        # 确保置信度在0-1范围内
        df["Signal_Confidence"] = df["Signal_Confidence"].clip(0, 1)

    def get_strategy_summary(self) -> Dict[str, Any]:
        """获取策略摘要"""
        summary = {
            "total_strategies": len(self.strategies),
            "enabled_strategies": sum(
                1 for config in self.strategy_configs.values() if config.enabled
            ),
            "strategies": {},
        }

        for name, config in self.strategy_configs.items():
            summary["strategies"][name] = {
                "enabled": config.enabled,
                "weight": config.weight,
                "parameters": config.parameters,
            }

        return summary

    def get_available_strategies(self) -> List[str]:
        """获取可用的策略列表"""
        return StrategyRegistry.list_strategies()

    def get_strategy_info(self, name: str) -> Dict[str, Any]:
        """获取策略信息"""
        if name not in StrategyRegistry._strategies:
            return {}

        strategy_class = StrategyRegistry.get(name)
        return {
            "name": name,
            "description": strategy_class.__doc__ or "",
            "required_indicators": strategy_class.required_indicators(),
            "default_parameters": {},
        }


# 工厂函数
def create_signal_manager(
    strategies_config: List[Dict[str, Any]] = None,
    indicator_configs: Dict[str, Any] = None,
) -> SignalManager:
    """创建信号管理器的工厂函数"""
    config = SignalManagerConfig(
        indicator_configs=indicator_configs or {},
        strategy_configs=strategies_config or [],
    )

    manager = SignalManager(config)

    # 添加策略
    for strategy_config_dict in strategies_config or []:
        strategy_config = StrategyConfig.from_dict(strategy_config_dict)
        manager.add_strategy(strategy_config)

    return manager
