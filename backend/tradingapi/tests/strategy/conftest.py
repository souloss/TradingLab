"""
测试配置文件
提供测试数据和共享的fixture
"""

import importlib
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from tradingapi.strategy.indicators import momentum, trend, volatility, volume
from tradingapi.strategy.indicators.base import IndicatorRegistry


def _register_all_indicators():
    """Helper function to register all indicators"""
    # Import and register momentum indicators
    from tradingapi.strategy.indicators.momentum import (MACD, KDJCalculator,
                                                         RSICalculator)

    IndicatorRegistry.register("RSI", RSICalculator)
    IndicatorRegistry.register("KDJ", KDJCalculator)
    IndicatorRegistry.register("MACD", MACD)

    # Import and register trend indicators
    from tradingapi.strategy.indicators.trend import (ExponentialMovingAverage,
                                                      MovingAverage)

    IndicatorRegistry.register("MA", MovingAverage)
    IndicatorRegistry.register("EMA", ExponentialMovingAverage)

    # Import and register volatility indicators
    from tradingapi.strategy.indicators.volatility import (AverageTrueRange,
                                                           BollingerBands)

    IndicatorRegistry.register("ATR", AverageTrueRange)
    IndicatorRegistry.register("BollingerBands", BollingerBands)

    # Import and register volume indicators
    from tradingapi.strategy.indicators.volume import VolumeIndicator

    IndicatorRegistry.register("Volume", VolumeIndicator)


@pytest.fixture(autouse=True)
def reset_indicator_registry():
    """重置指标注册表"""
    # 清空注册表
    print("Resetting IndicatorRegistry")
    original_indicators = IndicatorRegistry._indicators.copy()
    IndicatorRegistry._indicators = {}

    # Explicitly register all indicators
    _register_all_indicators()

    print(
        f"Available indicators after reset: {list(IndicatorRegistry._indicators.keys())}"
    )
    return original_indicators


@pytest.fixture(autouse=True)
def restore_indicator_registry(request):
    """恢复指标注册表"""
    # 获取reset fixture返回的原始指标
    original_indicators = request.getfixturevalue("reset_indicator_registry")
    yield
    # 测试结束后恢复原始状态
    IndicatorRegistry._indicators = original_indicators


@pytest.fixture
def registered_indicator_manager():
    """提供已注册指标的IndicatorManager实例"""
    from tradingapi.strategy.indicators.base import IndicatorManager

    return IndicatorManager()


# @pytest.fixture(autouse=True)
# def reset_indicator_registry():
#     """重置指标注册表"""
#     # 清空注册表
#     print("Resetting IndicatorRegistry")
#     original_indicators = IndicatorRegistry._indicators.copy()
#     IndicatorRegistry._indicators = {}

#     # 强制重新加载指标模块以确保注册
#     modules = [
#         "tradingapi.strategy.indicators.momentum",
#         "tradingapi.strategy.indicators.trend",
#         "tradingapi.strategy.indicators.volatility",
#         "tradingapi.strategy.indicators.volume",
#         "tradingapi.strategy.indicators.base",
#         "tradingapi.strategy.indicators",
#     ]

#     for module_name in modules:
#         module = importlib.import_module(module_name)
#         importlib.reload(module)  # 重新加载模块以触发注册

#     print(
#         f"Available indicators after reset: {list(IndicatorRegistry._indicators.keys())}"
#     )
#     return original_indicators


# @pytest.fixture(autouse=True)
# def restore_indicator_registry(request):
#     """恢复指标注册表"""
#     # 获取reset fixture返回的原始指标
#     original_indicators = request.getfixturevalue("reset_indicator_registry")
#     yield
#     # 测试结束后恢复原始状态
#     IndicatorRegistry._indicators = original_indicators


@pytest.fixture
def sample_ohlc_data():
    """生成用于测试的OHLCV数据"""
    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")

    # 生成基础价格序列
    base_price = 100
    price_changes = np.random.normal(0, 0.02, 100)
    prices = [base_price]

    for change in price_changes[1:]:
        prices.append(prices[-1] * (1 + change))

    # 生成OHLCV数据
    data = {
        "开盘": prices,
        "最高": [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        "最低": [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        "收盘": prices,
        "成交量": np.random.randint(100000, 500000, 100),
    }

    return pd.DataFrame(data, index=dates)


@pytest.fixture
def trend_data():
    """生成趋势明显的测试数据"""
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")

    # 生成上升趋势
    base_price = 100
    trend_factor = 0.001  # 每日上涨0.1%
    noise = np.random.normal(0, 0.01, 100)

    prices = [base_price]
    for i in range(1, 100):
        prices.append(prices[-1] * (1 + trend_factor + noise[i]))

    data = {
        "开盘": prices,
        "最高": [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
        "最低": [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
        "收盘": prices,
        "成交量": np.random.randint(100000, 500000, 100),
    }

    return pd.DataFrame(data, index=dates)


@pytest.fixture
def range_bound_data():
    """生成震荡市场的测试数据"""
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")

    # 生成震荡价格
    base_price = 100
    prices = []

    for i in range(100):
        # 使用正弦函数生成震荡价格
        price = base_price + 10 * np.sin(i * 0.2) + np.random.normal(0, 1)
        prices.append(price)

    data = {
        "开盘": prices,
        "最高": [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
        "最低": [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
        "收盘": prices,
        "成交量": np.random.randint(100000, 500000, 100),
    }

    return pd.DataFrame(data, index=dates)
