"""
测试基础数据结构和枚举
"""

import pandas as pd
import pytest

from tradingapi.strategy.base import (
    IndicatorCategory,
    IndicatorResult,
    MarketRegime,
    SignalResult,
    SignalType,
    StrategyConfig,
)


class TestSignalType:
    """测试信号类型枚举"""

    def test_signal_type_values(self):
        """测试信号类型值"""
        assert SignalType.BUY.value == 1
        assert SignalType.SELL.value == -1
        assert SignalType.NEUTRAL.value == 0


class TestMarketRegime:
    """测试市场状态枚举"""

    def test_market_regime_exists(self):
        """测试市场状态枚举存在"""
        assert hasattr(MarketRegime, "TRENDING_UP")
        assert hasattr(MarketRegime, "TRENDING_DOWN")
        assert hasattr(MarketRegime, "RANGING")
        assert hasattr(MarketRegime, "VOLATILE")


class TestIndicatorCategory:
    """测试指标类别枚举"""

    def test_indicator_category_exists(self):
        """测试指标类别枚举存在"""
        assert hasattr(IndicatorCategory, "TREND")
        assert hasattr(IndicatorCategory, "MOMENTUM")
        assert hasattr(IndicatorCategory, "VOLATILITY")
        assert hasattr(IndicatorCategory, "VOLUME")


class TestIndicatorResult:
    """测试指标结果类"""

    def test_indicator_result_creation(self):
        """测试指标结果创建"""
        data = pd.DataFrame(
            {"value": [1, 2, 3]}, index=pd.date_range("2023-01-01", periods=3)
        )
        result = IndicatorResult(name="test", values=data)

        assert result.name == "test"
        assert result.values.equals(data)
        assert result.metadata == {}

    def test_get_column(self):
        """测试获取列数据"""
        data = pd.DataFrame(
            {"value1": [1, 2, 3], "value2": [4, 5, 6]},
            index=pd.date_range("2023-01-01", periods=3),
        )

        result = IndicatorResult(name="test", values=data)
        column = result.get_column("value1")

        assert column.equals(data["value1"])

    def test_get_column_error(self):
        """测试获取不存在的列"""
        data = pd.DataFrame(
            {"value": [1, 2, 3]}, index=pd.date_range("2023-01-01", periods=3)
        )
        result = IndicatorResult(name="test", values=data)

        with pytest.raises(
            ValueError, match="Column not_found not found in indicator test"
        ):
            result.get_column("not_found")


class TestSignalResult:
    """测试信号结果类"""

    def test_signal_result_creation(self):
        """测试信号结果创建"""
        signals = pd.Series([0, 1, -1], index=pd.date_range("2023-01-01", periods=3))
        result = SignalResult(strategy_name="test", signals=signals)

        assert result.strategy_name == "test"
        assert result.signals.equals(signals)
        assert result.confidence is None
        assert result.metadata == {}

    def test_signal_result_with_confidence(self):
        """测试带置信度的信号结果"""
        signals = pd.Series([0, 1, -1], index=pd.date_range("2023-01-01", periods=3))
        confidence = pd.Series(
            [0.5, 0.7, 0.3], index=pd.date_range("2023-01-01", periods=3)
        )
        result = SignalResult(
            strategy_name="test", signals=signals, confidence=confidence
        )

        assert result.confidence.equals(confidence)

    def test_get_buy_signals(self):
        """测试获取买入信号"""
        # 明确创建测试数据
        dates = pd.date_range("2023-01-01", periods=4)
        signals = pd.Series([0, 1, -1, 1], index=dates)

        # 创建 SignalResult
        result = SignalResult(strategy_name="test", signals=signals)

        # 获取买入信号
        buy_signals = result.get_buy_signals()

        # 明确创建预期的买入信号
        expected_dates = [dates[1], dates[3]]  # 第2个和第4个日期
        expected = pd.Series([1, 1], index=expected_dates)

        # 验证结果
        assert buy_signals.equals(expected)

    def test_get_sell_signals(self):
        """测试获取卖出信号"""
        signals = pd.Series([0, 1, -1, 1], index=pd.date_range("2023-01-01", periods=4))
        result = SignalResult(strategy_name="test", signals=signals)

        sell_signals = result.get_sell_signals()
        expected = pd.Series(
            [-1], index=pd.date_range("2023-01-03", periods=1, freq="D")
        )

        assert sell_signals.equals(expected)


class TestStrategyConfig:
    """测试策略配置类"""

    def test_strategy_config_creation(self):
        """测试策略配置创建"""
        config = StrategyConfig(name="test")

        assert config.name == "test"
        assert config.enabled is True
        assert config.weight == 1.0
        assert config.parameters == {}

    def test_strategy_config_with_parameters(self):
        """测试带参数的策略配置"""
        parameters = {"param1": 1, "param2": "value"}
        config = StrategyConfig(name="test", parameters=parameters)

        assert config.parameters == parameters

    def test_from_dict(self):
        """测试从字典创建策略配置"""
        config_dict = {
            "name": "test",
            "enabled": False,
            "weight": 2.0,
            "parameters": {"param1": 1},
            "unknown_field": "value",  # 应该被过滤掉
        }

        config = StrategyConfig.from_dict(config_dict)

        assert config.name == "test"
        assert config.enabled is False
        assert config.weight == 2.0
        assert config.parameters == {"param1": 1}
        assert not hasattr(config, "unknown_field")

    def test_get_parameter(self):
        """测试获取参数值"""
        parameters = {"param1": 1, "param2": "value"}
        config = StrategyConfig(name="test", parameters=parameters)

        assert config.get_parameter("param1") == 1
        assert config.get_parameter("param2") == "value"
        assert config.get_parameter("nonexistent", "default") == "default"
        assert config.get_parameter("nonexistent") is None

    def test_set_parameter(self):
        """测试设置参数值"""
        config = StrategyConfig(name="test")

        config.set_parameter("param1", 1)
        assert config.get_parameter("param1") == 1

        config.set_parameter("param1", 2)
        assert config.get_parameter("param1") == 2

    def test_to_dict(self):
        """测试转换为字典"""
        parameters = {"param1": 1}
        config = StrategyConfig(
            name="test", enabled=False, weight=2.0, parameters=parameters
        )

        config_dict = config.to_dict()

        expected = {
            "name": "test",
            "enabled": False,
            "weight": 2.0,
            "parameters": parameters,
        }

        assert config_dict == expected
