"""
指标模块初始化文件
导入所有指标类，以便注册装饰器能够执行
"""

# 导入所有指标模块，这样装饰器会自动注册指标
from . import base, momentum, trend, volatility, volume
# 导出指标基类和注册机制
from .base import (IndicatorCalculator, IndicatorCategory, IndicatorManager,
                   IndicatorRegistry, register_indicator)

__all__ = [
    "IndicatorRegistry",
    "IndicatorManager",
    "register_indicator",
    "IndicatorCalculator",
    "IndicatorCategory",
]
