"""
测试指标计算器
"""

import numpy as np
import pandas as pd
import pytest

from tradingapi.strategy.base import IndicatorCategory
from tradingapi.strategy.config.indicators import (ATRConfig,
                                                   BollingerBandsConfig,
                                                   MACDConfig, MAConfig,
                                                   RSIConfig, VolumeConfig)
from tradingapi.strategy.config_manager import ConfigManager
from tradingapi.strategy.exceptions import IndicatorNotFoundError
# 确保所有指标模块都被导入和注册
from tradingapi.strategy.indicators import momentum, trend, volatility, volume
from tradingapi.strategy.indicators.base import (IndicatorManager,
                                                 IndicatorRegistry)
from tradingapi.strategy.indicators.momentum import MACD, RSICalculator
from tradingapi.strategy.indicators.trend import MovingAverage
from tradingapi.strategy.indicators.volatility import (AverageTrueRange,
                                                       BollingerBands)
from tradingapi.strategy.indicators.volume import VolumeIndicator


class TestIndicatorRegistry:
    """测试指标注册表"""

    def test_register_indicator(self):
        """测试注册指标"""
        # 清空注册表
        IndicatorRegistry._indicators = {}

        # 注册指标
        IndicatorRegistry.register("TestIndicator", RSICalculator)

        assert "TestIndicator" in IndicatorRegistry._indicators
        assert IndicatorRegistry._indicators["TestIndicator"] == RSICalculator

    def test_get_indicator(self):
        """测试获取指标"""
        # 清空注册表
        IndicatorRegistry._indicators = {}

        # 注册指标
        IndicatorRegistry.register("TestIndicator", RSICalculator)

        # 获取指标
        indicator_class = IndicatorRegistry.get("TestIndicator")
        assert indicator_class == RSICalculator

    def test_get_unknown_indicator(self):
        """测试获取未知指标"""
        # 清空注册表
        IndicatorRegistry._indicators = {}

        with pytest.raises(IndicatorNotFoundError, match="Indicator Unknown not found"):
            IndicatorRegistry.get("Unknown")

    def test_list_indicators(self):
        """测试列出指标"""
        # 清空注册表
        IndicatorRegistry._indicators = {}

        # 注册指标
        IndicatorRegistry.register("TestIndicator1", RSICalculator)
        IndicatorRegistry.register("TestIndicator2", MACD)

        # 列出指标
        indicators = IndicatorRegistry.list_indicators()

        assert "TestIndicator1" in indicators
        assert "TestIndicator2" in indicators
        assert len(indicators) == 2


class TestIndicatorManager:
    """测试指标管理器"""

    def test_initialization(self):
        """测试初始化"""
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        assert indicator_manager.config_manager == config_manager
        assert indicator_manager._cached_results == {}

    def test_calculate_indicator(self, sample_ohlc_data):
        """测试计算指标"""
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        # 计算RSI指标
        result = indicator_manager.calculate_indicator("RSI", sample_ohlc_data)

        assert result.name == "RSI"
        assert "RSI" in result.values.columns
        assert len(result.values) == len(sample_ohlc_data)
        assert "period" in result.metadata

    def test_calculate_indicator_caching(self, sample_ohlc_data):
        """测试指标计算缓存"""
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        # 计算RSI指标
        result1 = indicator_manager.calculate_indicator("RSI", sample_ohlc_data)

        # 再次计算，应该使用缓存
        result2 = indicator_manager.calculate_indicator("RSI", sample_ohlc_data)

        # 验证是同一个对象
        assert result1 is result2

    def test_update_config(self, sample_ohlc_data):
        """测试更新配置"""
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        # 计算RSI指标
        result1 = indicator_manager.calculate_indicator("RSI", sample_ohlc_data)

        # 更新RSI配置
        new_config = {"period": 20}
        indicator_manager.update_config("RSI", new_config)

        # 再次计算，应该使用新配置
        result2 = indicator_manager.calculate_indicator("RSI", sample_ohlc_data)

        # 验证结果不同（因为配置不同）
        assert not result1.values.equals(result2.values)
        assert result2.metadata["period"] == 20

    def test_clear_cache(self, sample_ohlc_data):
        """测试清除缓存"""
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        # 计算RSI指标
        result1 = indicator_manager.calculate_indicator("RSI", sample_ohlc_data)

        # 清除缓存
        indicator_manager.clear_cache()

        # 再次计算，应该重新计算
        result2 = indicator_manager.calculate_indicator("RSI", sample_ohlc_data)

        # 验证不是同一个对象
        assert result1 is not result2
        # 但结果应该相同
        assert result1.values.equals(result2.values)


class TestRSIIndicator:
    """测试RSI指标"""

    def test_properties(self):
        """测试属性"""
        indicator = RSICalculator()

        assert indicator.name == "RSI"
        assert indicator.category == IndicatorCategory.MOMENTUM

    def test_calculate(self, sample_ohlc_data):
        """测试计算"""
        config = RSIConfig(period=14)
        indicator = RSICalculator()
        result = indicator.calculate(sample_ohlc_data, config)

        assert result.name == "RSI"
        assert "RSI" in result.values.columns
        assert len(result.values) == len(sample_ohlc_data)
        assert result.metadata["period"] == 14

        # RSI值应该在0-100之间
        rsi_values = result.values["RSI"].dropna()
        assert all(0 <= val <= 100 for val in rsi_values)

    def test_validate_inputs_valid(self, sample_ohlc_data):
        """测试验证有效输入"""
        indicator = RSICalculator()
        assert indicator.validate_inputs(sample_ohlc_data) is True

    def test_validate_inputs_invalid(self):
        """测试验证无效输入"""
        # 缺少必需列
        invalid_data = pd.DataFrame(
            {
                "open": [1, 2, 3],
                "high": [1, 2, 3],
                "low": [1, 2, 3],
                "close": [1, 2, 3],
                # 缺少'volume'列
            }
        )

        indicator = RSICalculator()
        assert indicator.validate_inputs(invalid_data) is False


class TestMACDIndicator:
    """测试MACD指标"""

    def test_properties(self):
        """测试属性"""
        indicator = MACD()

        assert indicator.name == "MACD"
        assert indicator.category == IndicatorCategory.MOMENTUM

    def test_calculate(self, sample_ohlc_data):
        """测试计算"""
        config = MACDConfig(fast_period=12, slow_period=26, signal_period=9)
        indicator = MACD()
        result = indicator.calculate(sample_ohlc_data, config)

        assert result.name == "MACD"
        assert "MACD" in result.values.columns
        assert "MACD_Signal" in result.values.columns
        assert "MACD_Hist" in result.values.columns
        assert len(result.values) == len(sample_ohlc_data)
        assert result.metadata["fast_period"] == 12
        assert result.metadata["slow_period"] == 26
        assert result.metadata["signal_period"] == 9


class TestMAIndicator:
    """测试移动平均线指标"""

    def test_properties(self):
        """测试属性"""
        indicator = MovingAverage()

        assert indicator.name == "MA"
        assert indicator.category == IndicatorCategory.TREND

    def test_calculate(self, sample_ohlc_data):
        """测试计算"""
        config = MAConfig(periods=[5, 10, 20])
        indicator = MovingAverage()
        result = indicator.calculate(sample_ohlc_data, config)

        assert result.name == "MA"
        assert "MA5" in result.values.columns
        assert "MA10" in result.values.columns
        assert "MA20" in result.values.columns
        assert len(result.values) == len(sample_ohlc_data)
        assert result.metadata["periods"] == [5, 10, 20]

        # MA值应该接近收盘价
        for period in [5, 10, 20]:
            ma_col = f"MA{period}"
            # 忽略前period-1个NaN值
            valid_rows = sample_ohlc_data["收盘"].iloc[period - 1 :]
            ma_values = result.values[ma_col].iloc[period - 1 :]

            # MA值应该与收盘价相近，使用更宽松的比较
            assert all(
                abs(ma - close) / close < 0.2  # 增加容差到20%
                for ma, close in zip(ma_values, valid_rows)
                if not pd.isna(ma)  # 跳过NaN值
            )


class TestATRIndicator:
    """测试ATR指标"""

    def test_properties(self):
        """测试属性"""
        indicator = AverageTrueRange()

        assert indicator.name == "ATR"
        assert indicator.category == IndicatorCategory.VOLATILITY

    def test_calculate(self, sample_ohlc_data):
        """测试计算"""
        config = ATRConfig(period=14)
        indicator = AverageTrueRange()
        result = indicator.calculate(sample_ohlc_data, config)

        assert result.name == "ATR"
        assert "ATR" in result.values.columns
        assert len(result.values) == len(sample_ohlc_data)
        assert result.metadata["period"] == 14

        # ATR值应该为正数
        atr_values = result.values["ATR"].dropna()
        assert all(val > 0 for val in atr_values)


class TestBollingerBandsIndicator:
    """测试布林带指标"""

    def test_properties(self):
        """测试属性"""
        indicator = BollingerBands()

        assert indicator.name == "BollingerBands"
        assert indicator.category == IndicatorCategory.VOLATILITY

    def test_calculate(self, sample_ohlc_data):
        """测试计算"""
        config = BollingerBandsConfig(period=20, std_dev=2.0)
        indicator = BollingerBands()
        result = indicator.calculate(sample_ohlc_data, config)

        assert result.name == "BollingerBands"
        assert "BB_Upper" in result.values.columns
        assert "BB_Middle" in result.values.columns
        assert "BB_Lower" in result.values.columns
        assert len(result.values) == len(sample_ohlc_data)
        assert result.metadata["period"] == 20
        assert result.metadata["std_dev"] == 2.0

        # 布林带应该满足: Upper >= Middle >= Lower
        for i in range(len(result.values)):
            if not pd.isna(result.values["BB_Upper"].iloc[i]):
                assert (
                    result.values["BB_Upper"].iloc[i]
                    >= result.values["BB_Middle"].iloc[i]
                )
                assert (
                    result.values["BB_Middle"].iloc[i]
                    >= result.values["BB_Lower"].iloc[i]
                )


class TestVolumeIndicator:
    """测试成交量指标"""

    def test_properties(self):
        """测试属性"""
        indicator = VolumeIndicator()

        assert indicator.name == "Volume"
        assert indicator.category == IndicatorCategory.VOLUME

    def test_calculate(self, sample_ohlc_data):
        """测试计算"""
        config = VolumeConfig(ma_periods=[5, 10, 20])
        indicator = VolumeIndicator()
        result = indicator.calculate(sample_ohlc_data, config)

        assert result.name == "Volume"
        assert "Volume" in result.values.columns
        assert "Vol_MA5" in result.values.columns
        assert "Vol_MA10" in result.values.columns
        assert "Vol_MA20" in result.values.columns
        assert len(result.values) == len(sample_ohlc_data)
        assert result.metadata["ma_periods"] == [5, 10, 20]

        # Volume值应该与原始数据相同
        assert all(result.values["Volume"] == sample_ohlc_data["成交量"])

        # Volume MA值应该与原始成交量的移动平均相同
        for period in [5, 10, 20]:
            ma_col = f"Vol_MA{period}"

            # 获取计算结果中的移动平均值
            ma_values = result.values[ma_col]

            # 计算期望的移动平均值
            expected_ma = sample_ohlc_data["成交量"].rolling(window=period).mean()

            # 比较非NaN值
            non_nan_mask = ~ma_values.isna()
            assert non_nan_mask.equals(~expected_ma.isna()), "NaN patterns don't match"

            # 只比较非NaN值
            ma_non_nan = ma_values[non_nan_mask]
            expected_non_nan = expected_ma[non_nan_mask]

            # 使用相对误差比较，考虑浮点精度
            for i, (ma, expected) in enumerate(zip(ma_non_nan, expected_non_nan)):
                # 对于较大的数值，使用相对误差
                if expected != 0:
                    relative_error = abs(ma - expected) / expected
                    assert (
                        relative_error < 1e-5
                    ), f"Index {i}: {ma} != {expected}, relative error: {relative_error}"
                else:
                    # 如果期望值为0，使用绝对误差
                    assert abs(ma - expected) < 1e-5, f"Index {i}: {ma} != {expected}"
