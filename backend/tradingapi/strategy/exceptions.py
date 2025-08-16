"""
自定义异常类
"""


class StrategyError(Exception):
    """策略基础异常"""

    pass


class StrategyNotFoundError(StrategyError):
    """策略未找到异常"""

    pass


class IndicatorError(Exception):
    """指标基础异常"""

    pass


class IndicatorNotFoundError(IndicatorError):
    """指标未找到异常"""

    pass


class ConfigurationError(Exception):
    """配置错误异常"""

    pass
