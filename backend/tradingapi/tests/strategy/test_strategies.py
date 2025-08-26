"""
测试策略类
"""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from tradingapi.strategy.base import SignalResult, StrategyConfig
from tradingapi.strategy.config_manager import ConfigManager
from tradingapi.strategy.exceptions import StrategyError, StrategyNotFoundError
from tradingapi.strategy.indicators.base import IndicatorManager
from tradingapi.strategy.strategies.base import StrategyRegistry
from tradingapi.strategy.strategies.mean_reversion import BollingerBandsStrategy
from tradingapi.strategy.strategies.momentum import RSIStrategy
from tradingapi.strategy.strategies.trend_following import MACrossStrategy


class TestStrategyRegistry:
    """测试策略注册表"""

    def test_register_strategy(self):
        """测试注册策略"""
        # 清空注册表
        StrategyRegistry._strategies = {}

        # 注册策略
        StrategyRegistry.register("TestStrategy", RSIStrategy)

        assert "TestStrategy" in StrategyRegistry._strategies
        assert StrategyRegistry._strategies["TestStrategy"] == RSIStrategy

    def test_get_strategy(self):
        """测试获取策略"""
        # 清空注册表
        StrategyRegistry._strategies = {}

        # 注册策略
        StrategyRegistry.register("TestStrategy", RSIStrategy)

        # 获取策略
        strategy_class = StrategyRegistry.get("TestStrategy")
        assert strategy_class == RSIStrategy

    def test_get_unknown_strategy(self):
        """测试获取未知策略"""
        # 清空注册表
        StrategyRegistry._strategies = {}

        with pytest.raises(StrategyNotFoundError, match="Strategy Unknown not found"):
            StrategyRegistry.get("Unknown")

    def test_list_strategies(self):
        """测试列出策略"""
        # 清空注册表
        StrategyRegistry._strategies = {}

        # 注册策略
        StrategyRegistry.register("TestStrategy1", RSIStrategy)
        StrategyRegistry.register("TestStrategy2", MACrossStrategy)

        # 列出策略
        strategies = StrategyRegistry.list_strategies()

        assert "TestStrategy1" in strategies
        assert "TestStrategy2" in strategies
        assert len(strategies) == 2


class TestStrategyBase:
    """测试策略基类"""

    def test_initialization_with_config_manager(self, sample_ohlc_data):
        """测试带配置管理器的初始化"""
        config = StrategyConfig(name="RSI")
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        strategy = RSIStrategy(config, indicator_manager, config_manager)

        assert strategy.config == config
        assert strategy.name == "RSI"
        assert strategy.indicator_manager == indicator_manager
        assert strategy.config_manager == config_manager
        assert strategy.strategy_config is not None

    def test_initialization_without_config_manager(self, sample_ohlc_data):
        """测试不带配置管理器的初始化"""
        config = StrategyConfig(name="RSI")
        indicator_manager = MagicMock()

        strategy = RSIStrategy(config, indicator_manager)

        assert strategy.config == config
        assert strategy.name == "RSI"
        assert strategy.indicator_manager == indicator_manager
        assert strategy.config_manager is None
        assert strategy.strategy_config is not None

    def test_init_strategy_config_with_config_manager(self, sample_ohlc_data):
        """测试带配置管理器的策略配置初始化"""
        config = StrategyConfig(name="RSI")
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        strategy = RSIStrategy(config, indicator_manager, config_manager)

        # 策略配置应该从配置管理器获取
        assert strategy.strategy_config.oversold_threshold == 30  # 默认值
        assert strategy.strategy_config.overbought_threshold == 70  # 默认值
        assert strategy.strategy_config.lookback_period == 5  # 默认值

    def test_init_strategy_config_with_custom_parameters(self, sample_ohlc_data):
        """测试自定义参数的策略配置初始化"""
        config = StrategyConfig(
            name="RSI",
            parameters={
                "oversold_threshold": 25,
                "overbought_threshold": 75,
                "lookback_period": 3,
            },
        )
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        strategy = RSIStrategy(config, indicator_manager, config_manager)

        # 策略配置应该使用自定义参数
        assert strategy.strategy_config.oversold_threshold == 25
        assert strategy.strategy_config.overbought_threshold == 75
        assert strategy.strategy_config.lookback_period == 3

    def test_init_strategy_config_fallback_to_default(self, sample_ohlc_data):
        """测试策略配置初始化回退到默认值"""
        config = StrategyConfig(name="RSI")
        config_manager = MagicMock()
        config_manager.get_strategy_config.side_effect = Exception("Config error")
        indicator_manager = MagicMock()

        strategy = RSIStrategy(config, indicator_manager, config_manager)

        # 策略配置应该回退到默认值
        assert strategy.strategy_config.oversold_threshold == 30  # 默认值
        assert strategy.strategy_config.overbought_threshold == 70  # 默认值
        assert strategy.strategy_config.lookback_period == 5  # 默认值

    def test_prepare_indicators_success(self, sample_ohlc_data):
        """测试准备指标成功"""
        config = StrategyConfig(name="RSI")
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        strategy = RSIStrategy(config, indicator_manager, config_manager)

        # 准备指标
        df = sample_ohlc_data.copy()
        strategy.prepare_indicators(df)

        # 应该添加了RSI指标
        assert "RSI" in df.columns

    def test_prepare_indicators_failure(self, sample_ohlc_data):
        """测试准备指标失败"""
        config = StrategyConfig(name="RSI")
        config_manager = ConfigManager()

        # 创建一个会抛出异常的指标管理器
        indicator_manager = MagicMock()
        indicator_manager.calculate_indicator.side_effect = Exception(
            "Calculation error"
        )

        strategy = RSIStrategy(config, indicator_manager, config_manager)

        # 准备指标应该抛出异常
        df = sample_ohlc_data.copy()
        with pytest.raises(
            StrategyError, match="Missing required indicators: \\['RSI'\\]"
        ):
            strategy.prepare_indicators(df)

    def test_generate_signals_with_confidence(self, sample_ohlc_data):
        """测试生成带置信度的信号"""
        config = StrategyConfig(name="RSI")
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        strategy = RSIStrategy(config, indicator_manager, config_manager)

        # 准备指标
        df = sample_ohlc_data.copy()
        strategy.prepare_indicators(df)

        # 生成信号
        signal_result = strategy.generate_signals_with_confidence(df)

        assert isinstance(signal_result, SignalResult)
        assert signal_result.strategy_name == "RSI"
        assert isinstance(signal_result.signals, pd.Series)
        assert isinstance(signal_result.confidence, pd.Series)
        assert len(signal_result.signals) == len(df)
        assert len(signal_result.confidence) == len(df)

    def test_validate_parameters_success(self, sample_ohlc_data):
        """测试验证参数成功"""
        config = StrategyConfig(name="RSI")
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        strategy = RSIStrategy(config, indicator_manager, config_manager)

        # 验证参数应该成功
        assert strategy.validate_parameters() is True


class TestRSIStrategy:
    """测试RSI策略"""

    def test_get_default_config(self):
        """测试获取默认配置"""
        config = StrategyConfig(name="RSI")
        indicator_manager = MagicMock()

        strategy = RSIStrategy(config, indicator_manager)
        default_config = strategy.get_default_config()

        assert default_config.oversold_threshold == 30
        assert default_config.overbought_threshold == 70
        assert default_config.lookback_period == 5

    def test_required_indicators(self):
        """测试所需指标"""
        config = StrategyConfig(name="RSI")
        indicator_manager = MagicMock()

        strategy = RSIStrategy(config, indicator_manager)
        indicators = strategy.required_indicators()

        assert indicators == ["RSI"]

    def test_get_indicator_configs(self):
        """测试获取指标配置"""
        config = StrategyConfig(name="RSI")
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        strategy = RSIStrategy(config, indicator_manager, config_manager)
        indicator_configs = strategy.get_indicator_configs()

        assert "RSI" in indicator_configs
        assert indicator_configs["RSI"].period == 14  # 默认值

    def test_generate_signals(self, sample_ohlc_data):
        """测试生成信号"""
        config = StrategyConfig(name="RSI")
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        strategy = RSIStrategy(config, indicator_manager, config_manager)

        # 准备指标
        df = sample_ohlc_data.copy()
        strategy.prepare_indicators(df)

        # 生成信号
        signal_result = strategy.generate_signals(df)

        assert isinstance(signal_result, SignalResult)
        assert signal_result.strategy_name == "RSI"
        assert isinstance(signal_result.signals, pd.Series)
        assert len(signal_result.signals) == len(df)

        # 信号值应该只包含-1, 0, 1
        unique_signals = set(signal_result.signals.dropna().unique())
        assert unique_signals.issubset({-1, 0, 1})

        # 元数据应该包含策略参数
        assert "oversold_threshold" in signal_result.metadata
        assert "overbought_threshold" in signal_result.metadata
        assert "lookback_period" in signal_result.metadata

    def test_generate_signals_with_custom_parameters(self, sample_ohlc_data):
        """测试使用自定义参数生成信号"""
        config = StrategyConfig(
            name="RSI",
            parameters={
                "oversold_threshold": 25,
                "overbought_threshold": 75,
                "lookback_period": 3,
            },
        )
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        strategy = RSIStrategy(config, indicator_manager, config_manager)

        # 准备指标
        df = sample_ohlc_data.copy()
        strategy.prepare_indicators(df)

        # 生成信号
        signal_result = strategy.generate_signals(df)

        # 元数据应该包含自定义参数
        assert signal_result.metadata["oversold_threshold"] == 25
        assert signal_result.metadata["overbought_threshold"] == 75
        assert signal_result.metadata["lookback_period"] == 3


class TestMACrossStrategy:
    """测试均线交叉策略"""

    def test_get_default_config(self):
        """测试获取默认配置"""
        config = StrategyConfig(name="MA")
        indicator_manager = MagicMock()

        strategy = MACrossStrategy(config, indicator_manager)
        default_config = strategy.get_default_config()

        assert default_config.signal_threshold == 0.01
        assert default_config.ma_config.periods == [5, 10, 20, 60, 120]

    def test_required_indicators(self):
        """测试所需指标"""
        config = StrategyConfig(name="MA")
        indicator_manager = MagicMock()

        strategy = MACrossStrategy(config, indicator_manager)
        indicators = strategy.required_indicators()

        assert indicators == ["MA"]

    def test_get_indicator_configs(self):
        """测试获取指标配置"""
        config = StrategyConfig(name="MA")
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        strategy = MACrossStrategy(config, indicator_manager, config_manager)
        indicator_configs = strategy.get_indicator_configs()

        assert "MA" in indicator_configs
        assert indicator_configs["MA"].periods == [5, 10, 20, 60, 120]  # 默认值

    def test_generate_signals(self, sample_ohlc_data):
        """测试生成信号"""
        config = StrategyConfig(name="MA")
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        strategy = MACrossStrategy(config, indicator_manager, config_manager)

        # 准备指标
        df = sample_ohlc_data.copy()
        strategy.prepare_indicators(df)

        # 生成信号
        signal_result = strategy.generate_signals(df)

        assert isinstance(signal_result, SignalResult)
        assert signal_result.strategy_name == "MA"
        assert isinstance(signal_result.signals, pd.Series)
        assert len(signal_result.signals) == len(df)

        # 信号值应该只包含-1, 0, 1
        unique_signals = set(signal_result.signals.dropna().unique())
        assert unique_signals.issubset({-1, 0, 1})

        # 元数据应该包含策略参数
        assert "fast_period" in signal_result.metadata
        assert "slow_period" in signal_result.metadata
        assert "signal_threshold" in signal_result.metadata


class TestBollingerBandsStrategy:
    """测试布林带策略"""

    def test_get_default_config(self):
        """测试获取默认配置"""
        config = StrategyConfig(name="BollingerBands")
        indicator_manager = MagicMock()

        strategy = BollingerBandsStrategy(config, indicator_manager)
        default_config = strategy.get_default_config()

        assert default_config.entry_threshold == 0.8
        assert default_config.exit_threshold == 0.5
        assert default_config.bb_config.period == 20
        assert default_config.bb_config.std_dev == 2.0

    def test_required_indicators(self):
        """测试所需指标"""
        config = StrategyConfig(name="BollingerBands")
        indicator_manager = MagicMock()

        strategy = BollingerBandsStrategy(config, indicator_manager)
        indicators = strategy.required_indicators()

        assert indicators == ["BollingerBands"]

    def test_get_indicator_configs(self):
        """测试获取指标配置"""
        config = StrategyConfig(name="BollingerBands")
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        strategy = BollingerBandsStrategy(config, indicator_manager, config_manager)
        indicator_configs = strategy.get_indicator_configs()

        assert "BollingerBands" in indicator_configs
        assert indicator_configs["BollingerBands"].period == 20  # 默认值
        assert indicator_configs["BollingerBands"].std_dev == 2.0  # 默认值

    def test_generate_signals(self, sample_ohlc_data):
        """测试生成信号"""
        config = StrategyConfig(name="BollingerBands")
        config_manager = ConfigManager()
        indicator_manager = IndicatorManager(config_manager)

        strategy = BollingerBandsStrategy(config, indicator_manager, config_manager)

        # 准备指标
        df = sample_ohlc_data.copy()
        strategy.prepare_indicators(df)

        # 生成信号
        signal_result = strategy.generate_signals(df)

        assert isinstance(signal_result, SignalResult)
        assert signal_result.strategy_name == "BollingerBands"
        assert isinstance(signal_result.signals, pd.Series)
        assert len(signal_result.signals) == len(df)

        # 信号值应该只包含-1, 0, 1
        unique_signals = set(signal_result.signals.dropna().unique())
        assert unique_signals.issubset({-1, 0, 1})

        # 元数据应该包含策略参数
        assert "period" in signal_result.metadata
        assert "std_dev" in signal_result.metadata
        assert "entry_threshold" in signal_result.metadata
        assert "exit_threshold" in signal_result.metadata
