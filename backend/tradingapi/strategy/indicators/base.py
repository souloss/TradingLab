"""
技术指标基类和接口定义
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Type, TypeVar

import pandas as pd

from tradingapi.fetcher.interface import OHLCVExtendedSchema

from ..base import IndicatorCategory, IndicatorResult
from ..config_manager import ConfigManager
from ..exceptions import IndicatorNotFoundError

# 定义配置类的类型变量
TConfig = TypeVar("TConfig")


class IndicatorCalculator(ABC, Generic[TConfig]):
    """技术指标计算器基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """指标名称"""

    @property
    @abstractmethod
    def category(self) -> IndicatorCategory:
        """指标类别"""

    @abstractmethod
    def calculate(self, df: pd.DataFrame, config: TConfig) -> IndicatorResult:
        """计算技术指标"""

    def validate_inputs(self, df: pd.DataFrame) -> bool:
        """验证输入数据"""
        required_columns = [
            OHLCVExtendedSchema.open,
            OHLCVExtendedSchema.high,
            OHLCVExtendedSchema.low,
            OHLCVExtendedSchema.close,
            OHLCVExtendedSchema.volume,
        ]
        return all(col in df.columns for col in required_columns)


class IndicatorRegistry:
    """指标注册表"""

    _indicators: Dict[str, Type[IndicatorCalculator]] = {}

    @classmethod
    def register(cls, name: str, indicator_class: Type[IndicatorCalculator]):
        """注册指标计算器"""
        cls._indicators[name] = indicator_class

    @classmethod
    def get(cls, name: str) -> Type[IndicatorCalculator]:
        """获取指标计算器"""
        if name not in cls._indicators:
            raise IndicatorNotFoundError(f"Indicator {name} not found")
        return cls._indicators[name]

    @classmethod
    def list_indicators(cls) -> List[str]:
        """列出所有注册的指标"""
        return list(cls._indicators.keys())

    @classmethod
    def get_indicators_by_category(cls, category: IndicatorCategory) -> List[str]:
        """按类别获取指标"""
        return [
            name
            for name, indicator_class in cls._indicators.items()
            if indicator_class().category == category
        ]


def register_indicator(name: str):
    """指标注册装饰器"""

    def decorator(cls):
        IndicatorRegistry.register(name, cls)
        return cls

    return decorator


class IndicatorManager:
    """指标管理器"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._cached_results = {}

    def calculate_indicator(self, name: str, df: pd.DataFrame) -> IndicatorResult:
        """计算指定指标"""
        # 检查缓存
        cache_key = f"{name}_{hash(tuple(df.index))}"
        if cache_key in self._cached_results:
            return self._cached_results[cache_key]

        # 获取指标计算器
        indicator_class = IndicatorRegistry.get(name)
        indicator = indicator_class()

        # 获取配置
        config = self.config_manager.get_indicator_config(name)

        # 计算指标
        result = indicator.calculate(df, config=config)

        # 缓存结果
        self._cached_results[cache_key] = result

        return result

    def update_config(self, name: str, config: Dict[str, Any]):
        """更新指标配置"""
        self.config_manager.update_indicator_config(name, config)
        # 清除相关缓存
        keys_to_remove = [k for k in self._cached_results.keys() if k.startswith(name)]
        for key in keys_to_remove:
            del self._cached_results[key]

    def clear_cache(self):
        """清除所有缓存"""
        self._cached_results.clear()
