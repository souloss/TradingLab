"""
策略模块初始化文件
导入所有策略类，以便注册装饰器能够执行
"""

# 导入所有策略模块，这样装饰器会自动注册策略
# 导出策略基类和注册机制
from .base import (
    MeanReversionStrategy,
    MomentumStrategy,
    StrategyBase,
    StrategyRegistry,
    TrendStrategy,
    register_strategy,
)

__all__ = [
    "StrategyBase",
    "TrendStrategy",
    "MomentumStrategy",
    "MeanReversionStrategy",
    "StrategyRegistry",
    "register_strategy",
]
