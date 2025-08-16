"""
测试信号管理器
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from tradingapi.strategy.base import SignalType, StrategyConfig
from tradingapi.strategy.config_manager import ConfigManager
from tradingapi.strategy.exceptions import StrategyNotFoundError
from tradingapi.strategy.indicators.base import IndicatorManager
from tradingapi.strategy.manager import (SignalManager, SignalManagerConfig,
                                         create_signal_manager)


class TestSignalManagerConfig:
    """测试信号管理器配置"""

    def test_default_values(self):
        """测试默认值"""
        config = SignalManagerConfig()

        assert config.indicator_configs == {}
        assert config.strategy_configs == []

    def test_custom_values(self):
        """测试自定义值"""
        indicator_configs = {"MA": {"periods": [10, 20]}}
        strategy_configs = [{"name": "RSI", "parameters": {"period": 14}}]

        config = SignalManagerConfig(
            indicator_configs=indicator_configs, strategy_configs=strategy_configs
        )

        assert config.indicator_configs == indicator_configs
        assert config.strategy_configs == strategy_configs


class TestSignalManager:
    """测试信号管理器"""

    def test_initialization(self):
        """测试初始化"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        assert isinstance(signal_manager.config_manager, ConfigManager)
        assert isinstance(signal_manager.indicator_manager, IndicatorManager)
        assert signal_manager.strategies == {}
        assert signal_manager.strategy_configs == {}

    def test_initialization_with_config(self, sample_ohlc_data):
        """测试带配置的初始化"""
        indicator_configs = {"MA": {"periods": [10, 20]}}
        strategy_configs = [{"name": "RSI", "parameters": {"period": 14}}]
        config = SignalManagerConfig(
            indicator_configs=indicator_configs, strategy_configs=strategy_configs
        )
        signal_manager = SignalManager(config)

        # 验证指标配置已更新
        ma_config = signal_manager.config_manager.get_indicator_config("MA")
        assert ma_config.periods == [10, 20]

        # 验证策略已添加
        assert "RSI" in signal_manager.strategies
        assert "RSI" in signal_manager.strategy_configs

        # 验证策略配置
        rsi_strategy = signal_manager.strategies["RSI"]
        assert rsi_strategy.strategy_config.rsi_config.period == 14

    def test_add_strategy_success(self, sample_ohlc_data):
        """测试添加策略成功"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        strategy_config = StrategyConfig(name="RSI")
        result = signal_manager.add_strategy(strategy_config)

        assert result is True
        assert "RSI" in signal_manager.strategies
        assert "RSI" in signal_manager.strategy_configs

    def test_add_strategy_unknown(self, sample_ohlc_data):
        """测试添加未知策略"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        strategy_config = StrategyConfig(name="UnknownStrategy")
        result = signal_manager.add_strategy(strategy_config)

        assert result is False
        assert "UnknownStrategy" not in signal_manager.strategies

    def test_remove_strategy(self, sample_ohlc_data):
        """测试移除策略"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        # 添加策略
        strategy_config = StrategyConfig(name="RSI")
        signal_manager.add_strategy(strategy_config)

        # 移除策略
        result = signal_manager.remove_strategy("RSI")

        assert result is True
        assert "RSI" not in signal_manager.strategies
        assert "RSI" not in signal_manager.strategy_configs

    def test_remove_unknown_strategy(self, sample_ohlc_data):
        """测试移除未知策略"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        result = signal_manager.remove_strategy("UnknownStrategy")

        assert result is False

    def test_enable_strategy(self, sample_ohlc_data):
        """测试启用策略"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        # 添加策略
        strategy_config = StrategyConfig(name="RSI", enabled=False)
        signal_manager.add_strategy(strategy_config)

        # 启用策略
        result = signal_manager.enable_strategy("RSI", True)

        assert result is True
        assert signal_manager.strategy_configs["RSI"].enabled is True

    def test_disable_strategy(self, sample_ohlc_data):
        """测试禁用策略"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        # 添加策略
        strategy_config = StrategyConfig(name="RSI", enabled=True)
        signal_manager.add_strategy(strategy_config)

        # 禁用策略
        result = signal_manager.enable_strategy("RSI", False)

        assert result is True
        assert signal_manager.strategy_configs["RSI"].enabled is False

    def test_enable_unknown_strategy(self, sample_ohlc_data):
        """测试启用未知策略"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        result = signal_manager.enable_strategy("UnknownStrategy", True)

        assert result is False

    def test_set_strategy_weight(self, sample_ohlc_data):
        """测试设置策略权重"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        # 添加策略
        strategy_config = StrategyConfig(name="RSI")
        signal_manager.add_strategy(strategy_config)

        # 设置权重
        result = signal_manager.set_strategy_weight("RSI", 2.0)

        assert result is True
        assert signal_manager.strategy_configs["RSI"].weight == 2.0

    def test_set_strategy_weight_limits(self, sample_ohlc_data):
        """测试设置策略权重限制"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        # 添加策略
        strategy_config = StrategyConfig(name="RSI")
        signal_manager.add_strategy(strategy_config)

        # 设置超出范围的权重
        signal_manager.set_strategy_weight("RSI", -1.0)
        assert signal_manager.strategy_configs["RSI"].weight == 0.0

        signal_manager.set_strategy_weight("RSI", 15.0)
        assert signal_manager.strategy_configs["RSI"].weight == 10.0

    def test_set_unknown_strategy_weight(self, sample_ohlc_data):
        """测试设置未知策略权重"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        result = signal_manager.set_strategy_weight("UnknownStrategy", 2.0)

        assert result is False

    def test_update_indicator_config(self, sample_ohlc_data):
        """测试更新指标配置"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        # 更新MA配置
        new_config = {"periods": [10, 20, 30]}
        signal_manager.update_indicator_config("MA", new_config)

        # 验证配置已更新
        ma_config = signal_manager.config_manager.get_indicator_config("MA")
        assert ma_config.periods == [10, 20, 30]

    def test_generate_signals(self, sample_ohlc_data):
        """测试生成信号"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        # 添加策略
        rsi_config = StrategyConfig(name="RSI")
        signal_manager.add_strategy(rsi_config)

        # 生成信号
        result_df = signal_manager.generate_signals(sample_ohlc_data)

        # 验证结果
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == len(sample_ohlc_data)

        # 应该添加了信号列
        assert "Signal_RSI" in result_df.columns
        assert "Confidence_RSI" in result_df.columns

        # 应该添加了综合信号列
        assert "Signal_Combined" in result_df.columns
        assert "Signal_Confidence" in result_df.columns

        # 信号值应该只包含-1, 0, 1
        unique_signals = set(result_df["Signal_RSI"].dropna().unique())
        assert unique_signals.issubset({-1, 0, 1})

        # 置信度值应该在0-1之间
        confidence_values = result_df["Confidence_RSI"].dropna()
        assert all(0 <= val <= 1 for val in confidence_values)

    def test_generate_signals_with_disabled_strategy(self, sample_ohlc_data):
        """测试生成信号时禁用策略"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        # 添加策略但禁用
        rsi_config = StrategyConfig(name="RSI", enabled=False)
        signal_manager.add_strategy(rsi_config)

        # 生成信号
        result_df = signal_manager.generate_signals(sample_ohlc_data)

        # 验证结果
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == len(sample_ohlc_data)

        # 应该添加了信号列，但所有值应该是中性信号
        assert "Signal_RSI" in result_df.columns
        assert all(result_df["Signal_RSI"] == SignalType.NEUTRAL.value)

        # 置信度应该是0
        assert "Confidence_RSI" in result_df.columns
        assert all(result_df["Confidence_RSI"] == 0.0)

    def test_generate_signals_with_multiple_strategies(self, sample_ohlc_data):
        """测试生成多个策略的信号"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        # 添加多个策略
        rsi_config = StrategyConfig(name="RSI", weight=1.0)
        ma_config = StrategyConfig(name="MA", weight=2.0)
        signal_manager.add_strategy(rsi_config)
        signal_manager.add_strategy(ma_config)

        # 生成信号
        result_df = signal_manager.generate_signals(sample_ohlc_data)

        # 验证结果
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == len(sample_ohlc_data)

        # 应该添加了两个策略的信号列
        assert "Signal_RSI" in result_df.columns
        assert "Signal_MA" in result_df.columns
        assert "Confidence_RSI" in result_df.columns
        assert "Confidence_MA" in result_df.columns

        # 应该添加了综合信号列
        assert "Signal_Combined" in result_df.columns
        assert "Signal_Confidence" in result_df.columns

        # 综合信号应该考虑了权重
        # 由于MA权重是RSI的两倍，综合信号应该更接近MA信号
        combined_signals = result_df["Signal_Combined"].dropna()
        ma_signals = result_df["Signal_MA"].dropna()
        rsi_signals = result_df["Signal_RSI"].dropna()

        # 验证综合信号是加权平均
        for i in range(len(combined_signals)):
            expected = (ma_signals.iloc[i] * 2.0 + rsi_signals.iloc[i] * 1.0) / 3.0
            assert abs(combined_signals.iloc[i] - expected) < 1e-10

    def test_generate_signals_with_strategy_error(self, sample_ohlc_data):
        """测试生成信号时策略出错"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        # 添加策略，但模拟策略生成信号时出错
        rsi_config = StrategyConfig(name="RSI")
        signal_manager.add_strategy(rsi_config)

        # 修改策略的generate_signals方法，使其抛出异常
        original_method = signal_manager.strategies["RSI"].generate_signals

        def mock_generate_signals(df):
            raise Exception("Strategy error")

        signal_manager.strategies["RSI"].generate_signals = mock_generate_signals

        # 生成信号
        result_df = signal_manager.generate_signals(sample_ohlc_data)

        # 验证结果
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == len(sample_ohlc_data)

        # 应该添加了信号列，但所有值应该是中性信号
        assert "Signal_RSI" in result_df.columns
        assert all(result_df["Signal_RSI"] == SignalType.NEUTRAL.value)

        # 置信度应该是0
        assert "Confidence_RSI" in result_df.columns
        assert all(result_df["Confidence_RSI"] == 0.0)

    def test_get_strategy_summary(self, sample_ohlc_data):
        """测试获取策略摘要"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        # 添加策略
        rsi_config = StrategyConfig(name="RSI", enabled=False, weight=2.0)
        ma_config = StrategyConfig(name="MA", enabled=True, weight=1.5)
        signal_manager.add_strategy(rsi_config)
        signal_manager.add_strategy(ma_config)

        # 获取策略摘要
        summary = signal_manager.get_strategy_summary()

        # 验证摘要
        assert summary["total_strategies"] == 2
        assert summary["enabled_strategies"] == 1
        assert "RSI" in summary["strategies"]
        assert "MA" in summary["strategies"]

        # 验证策略详情
        assert summary["strategies"]["RSI"]["enabled"] is False
        assert summary["strategies"]["RSI"]["weight"] == 2.0
        assert summary["strategies"]["MA"]["enabled"] is True
        assert summary["strategies"]["MA"]["weight"] == 1.5

    def test_get_available_strategies(self, sample_ohlc_data):
        """测试获取可用策略列表"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        # 获取可用策略
        strategies = signal_manager.get_available_strategies()

        # 验证结果
        assert isinstance(strategies, list)
        assert "RSI" in strategies
        assert "MA" in strategies
        assert "MACD" in strategies

    def test_get_strategy_info(self, sample_ohlc_data):
        """测试获取策略信息"""
        config = SignalManagerConfig()
        signal_manager = SignalManager(config)

        # 获取策略信息
        info = signal_manager.get_strategy_info("RSI")

        # 验证结果
        assert isinstance(info, dict)
        assert info["name"] == "RSI"
        assert "description" in info
        assert "required_indicators" in info
        assert "default_parameters" in info
        assert info["required_indicators"] == ["RSI"]

        # 获取未知策略信息
        unknown_info = signal_manager.get_strategy_info("UnknownStrategy")
        assert unknown_info == {}


class TestCreateSignalManager:
    """测试创建信号管理器的工厂函数"""

    def test_create_signal_manager_default(self):
        """测试创建默认信号管理器"""
        signal_manager = create_signal_manager()

        assert isinstance(signal_manager, SignalManager)
        assert isinstance(signal_manager.config_manager, ConfigManager)
        assert isinstance(signal_manager.indicator_manager, IndicatorManager)
        assert signal_manager.strategies == {}
        assert signal_manager.strategy_configs == {}

    def test_create_signal_manager_with_configs(self):
        """测试带配置创建信号管理器"""
        indicator_configs = {"MA": {"periods": [10, 20]}}
        strategy_configs = [
            {"name": "RSI", "parameters": {"period": 14}},
            {"name": "MA", "enabled": False},
        ]

        signal_manager = create_signal_manager(
            strategies_config=strategy_configs, indicator_configs=indicator_configs
        )

        # 验证指标配置已更新
        ma_config = signal_manager.config_manager.get_indicator_config("MA")
        assert ma_config.periods == [10, 20]

        # 验证策略已添加
        assert "RSI" in signal_manager.strategies
        assert "MA" in signal_manager.strategies

        # 验证策略配置
        assert signal_manager.strategy_configs["RSI"].enabled is True
        assert signal_manager.strategy_configs["MA"].enabled is False
