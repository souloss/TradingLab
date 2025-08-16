"""
测试配置管理器
"""

import pytest

from tradingapi.strategy.config.indicators import MAConfig, RSIConfig
from tradingapi.strategy.config.strategies import RSIStrategyConfig
from tradingapi.strategy.config_manager import ConfigManager
from tradingapi.strategy.exceptions import ConfigurationError


class TestConfigManager:
    """测试配置管理器"""

    def test_initialization(self):
        """测试初始化"""
        config_manager = ConfigManager()

        # 检查指标配置
        assert "MA" in config_manager.indicator_configs
        assert "RSI" in config_manager.indicator_configs
        assert isinstance(config_manager.indicator_configs["MA"], MAConfig)
        assert isinstance(config_manager.indicator_configs["RSI"], RSIConfig)

        # 检查策略配置
        assert "RSI" in config_manager.strategy_configs
        assert isinstance(config_manager.strategy_configs["RSI"], RSIStrategyConfig)

    def test_get_indicator_config(self):
        """测试获取指标配置"""
        config_manager = ConfigManager()

        ma_config = config_manager.get_indicator_config("MA")
        assert isinstance(ma_config, MAConfig)

    def test_get_indicator_config_unknown(self):
        """测试获取未知指标配置"""
        config_manager = ConfigManager()

        with pytest.raises(ConfigurationError, match="Unknown indicator: Unknown"):
            config_manager.get_indicator_config("Unknown")

    def test_get_strategy_config(self):
        """测试获取策略配置"""
        config_manager = ConfigManager()

        rsi_strategy_config = config_manager.get_strategy_config("RSI")
        assert isinstance(rsi_strategy_config, RSIStrategyConfig)

    def test_get_strategy_config_unknown(self):
        """测试获取未知策略配置"""
        config_manager = ConfigManager()

        with pytest.raises(ConfigurationError, match="Unknown strategy: Unknown"):
            config_manager.get_strategy_config("Unknown")

    def test_update_indicator_config(self):
        """测试更新指标配置"""
        config_manager = ConfigManager()

        # 更新MA配置
        new_ma_config = {"periods": [10, 20, 30]}
        config_manager.update_indicator_config("MA", new_ma_config)

        # 验证更新
        updated_config = config_manager.get_indicator_config("MA")
        assert updated_config.periods == [10, 20, 30]

    def test_update_indicator_config_unknown(self):
        """测试更新未知指标配置"""
        config_manager = ConfigManager()

        with pytest.raises(ConfigurationError, match="Unknown indicator: Unknown"):
            config_manager.update_indicator_config("Unknown", {})

    def test_update_indicator_config_invalid(self):
        """测试更新无效指标配置"""
        config_manager = ConfigManager()

        # 无效的MA配置（非正周期）
        invalid_ma_config = {"periods": [10, -5, 30]}

        with pytest.raises(ValueError, match="All periods must be positive integers"):
            config_manager.update_indicator_config("MA", invalid_ma_config)

    def test_update_strategy_config(self):
        """测试更新策略配置"""
        config_manager = ConfigManager()

        # 更新RSI策略配置
        new_rsi_config = {
            "oversold_threshold": 25,
            "overbought_threshold": 75,
            "lookback_period": 3,
        }
        config_manager.update_strategy_config("RSI", new_rsi_config)

        # 验证更新
        updated_config = config_manager.get_strategy_config("RSI")
        assert updated_config.oversold_threshold == 25
        assert updated_config.overbought_threshold == 75
        assert updated_config.lookback_period == 3

    def test_update_strategy_config_unknown(self):
        """测试更新未知策略配置"""
        config_manager = ConfigManager()

        with pytest.raises(ConfigurationError, match="Unknown strategy: Unknown"):
            config_manager.update_strategy_config("Unknown", {})

    def test_update_strategy_config_invalid(self):
        """测试更新无效策略配置"""
        config_manager = ConfigManager()

        # 无效的RSI策略配置（超卖阈值大于超买阈值）
        invalid_rsi_config = {"oversold_threshold": 70, "overbought_threshold": 30}

        with pytest.raises(
            ValueError,
            match="oversold_threshold must be less than overbought_threshold",
        ):
            config_manager.update_strategy_config("RSI", invalid_rsi_config)

    def test_to_dict(self):
        """测试转换为字典"""
        config_manager = ConfigManager()

        config_dict = config_manager.to_dict()

        # 检查结构
        assert "indicators" in config_dict
        assert "strategies" in config_dict

        # 检查指标配置
        assert "MA" in config_dict["indicators"]
        assert "periods" in config_dict["indicators"]["MA"]

        # 检查策略配置
        assert "RSI" in config_dict["strategies"]
        assert "oversold_threshold" in config_dict["strategies"]["RSI"]

    def test_from_dict(self):
        """测试从字典加载配置"""
        config_manager = ConfigManager()

        # 准备配置字典
        config_dict = {
            "indicators": {"MA": {"periods": [10, 20, 30]}, "RSI": {"period": 20}},
            "strategies": {
                "RSI": {
                    "oversold_threshold": 25,
                    "overbought_threshold": 75,
                    "lookback_period": 3,
                }
            },
        }

        # 加载配置
        config_manager.from_dict(config_dict)

        # 验证指标配置
        ma_config = config_manager.get_indicator_config("MA")
        assert ma_config.periods == [10, 20, 30]

        rsi_config = config_manager.get_indicator_config("RSI")
        assert rsi_config.period == 20

        # 验证策略配置
        rsi_strategy_config = config_manager.get_strategy_config("RSI")
        assert rsi_strategy_config.oversold_threshold == 25
        assert rsi_strategy_config.overbought_threshold == 75
        assert rsi_strategy_config.lookback_period == 3

    def test_from_dict_partial(self):
        """测试从部分配置字典加载配置"""
        config_manager = ConfigManager()

        # 只更新部分配置
        config_dict = {"indicators": {"MA": {"periods": [10, 20, 30]}}}

        # 加载配置
        config_manager.from_dict(config_dict)

        # 验证MA配置已更新
        ma_config = config_manager.get_indicator_config("MA")
        assert ma_config.periods == [10, 20, 30]

        # 验证RSI配置保持默认值
        rsi_config = config_manager.get_indicator_config("RSI")
        assert rsi_config.period == 14  # 默认值
