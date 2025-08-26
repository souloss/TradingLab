"""
测试配置类
"""

from dataclasses import dataclass, field
from typing import Dict, List

import pytest

from tradingapi.strategy.config.base import BaseConfig
from tradingapi.strategy.config.indicators import MAConfig, RSIConfig
from tradingapi.strategy.config.strategies import (
    MACrossStrategyConfig,
    RSIStrategyConfig,
)
from tradingapi.strategy.exceptions import ConfigurationError


class TestBaseConfig:
    """测试基础配置类"""

    def test_base_config_creation(self):
        """测试基础配置创建"""
        config = BaseConfig()
        assert config is not None

    def test_from_dict_empty(self):
        """测试从空字典创建配置"""
        config = BaseConfig.from_dict({})
        assert config is not None

    def test_from_dict_with_valid_fields(self):
        """测试从有效字段字典创建配置"""

        # 创建一个简单的测试配置类
        @dataclass
        class TestConfig(BaseConfig):
            value: int = 10

        config_dict = {"value": 20}
        config = TestConfig.from_dict(config_dict)

        assert config.value == 20

    def test_from_dict_with_invalid_fields(self):
        """测试从无效字段字典创建配置"""

        @dataclass
        class TestConfig(BaseConfig):
            value: int = 10

        config_dict = {"value": 20, "invalid_field": "value"}
        config = TestConfig.from_dict(config_dict)

        assert config.value == 20
        assert not hasattr(config, "invalid_field")

    def test_from_dict_type_error(self):
        """测试类型错误"""

        @dataclass
        class TestConfig(BaseConfig):
            value: int = 10

        config_dict = {"value": "not_an_int"}

        # 应该抛出ConfigurationError
        with pytest.raises(
            ConfigurationError,
            match="Invalid configuration for TestConfig: Field 'value': expected <class 'int'>, got <class 'str'>",
        ):
            TestConfig.from_dict(config_dict)

    def test_from_dict_optional_type(self):
        """测试Optional类型"""
        from typing import Optional

        @dataclass
        class TestConfig(BaseConfig):
            value: Optional[int] = None

        # None值应该通过
        config_dict = {"value": None}
        config = TestConfig.from_dict(config_dict)
        assert config.value is None

        # 正确的类型应该通过
        config_dict = {"value": 10}
        config = TestConfig.from_dict(config_dict)
        assert config.value == 10

        # 错误的类型应该失败
        config_dict = {"value": "not_an_int"}
        with pytest.raises(ConfigurationError):
            TestConfig.from_dict(config_dict)

    def test_from_dict_list_type(self):
        """测试List类型"""

        @dataclass
        class TestConfig(BaseConfig):
            values: List[int] = field(default_factory=list)

        # 正确的类型应该通过
        config_dict = {"values": [1, 2, 3]}
        config = TestConfig.from_dict(config_dict)
        assert config.values == [1, 2, 3]

        # 错误的类型应该失败
        config_dict = {"values": [1, "2", 3]}
        with pytest.raises(ConfigurationError):
            TestConfig.from_dict(config_dict)

        # 非列表类型应该失败
        config_dict = {"values": "not_a_list"}
        with pytest.raises(ConfigurationError):
            TestConfig.from_dict(config_dict)

    def test_from_dict_dict_type(self):
        """测试Dict类型"""

        @dataclass
        class TestConfig(BaseConfig):
            mapping: Dict[str, int] = field(default_factory=dict)

        # 正确的类型应该通过
        config_dict = {"mapping": {"a": 1, "b": 2}}
        config = TestConfig.from_dict(config_dict)
        assert config.mapping == {"a": 1, "b": 2}

        # 错误的值类型应该失败
        config_dict = {"mapping": {"a": "1", "b": 2}}
        with pytest.raises(ConfigurationError):
            TestConfig.from_dict(config_dict)

        # 非字典类型应该失败
        config_dict = {"mapping": "not_a_dict"}
        with pytest.raises(ConfigurationError):
            TestConfig.from_dict(config_dict)

    def test_from_dict_numeric_conversion(self):
        """测试数值类型转换"""

        @dataclass
        class TestConfig(BaseConfig):
            int_value: int = 0
            float_value: float = 0.0

        # int可以接受float值，如果它是整数
        config_dict = {"int_value": 10.0}
        config = TestConfig.from_dict(config_dict)
        assert config.int_value == 10

        # float可以接受int值
        config_dict = {"float_value": 10}
        config = TestConfig.from_dict(config_dict)
        assert config.float_value == 10.0

        # int不能接受非整数float值
        config_dict = {"int_value": 10.5}
        with pytest.raises(ConfigurationError):
            TestConfig.from_dict(config_dict)

    def test_to_dict(self):
        """测试转换为字典"""

        @dataclass
        class TestConfig(BaseConfig):
            value: int = 10

        config = TestConfig(value=20)
        config_dict = config.to_dict()

        assert config_dict == {"value": 20}

    def test_update(self):
        """测试更新配置"""

        @dataclass
        class TestConfig(BaseConfig):
            value1: int = 10
            value2: str = "default"

        config = TestConfig()
        config.update({"value1": 20, "value2": "updated"})

        assert config.value1 == 20
        assert config.value2 == "updated"


class TestMAConfig:
    """测试移动平均线配置"""

    def test_default_values(self):
        """测试默认值"""
        config = MAConfig()
        assert config.periods == [5, 10, 20, 60, 120]

    def test_custom_periods(self):
        """测试自定义周期"""
        config = MAConfig(periods=[10, 20, 30])
        assert config.periods == [10, 20, 30]

    def test_validate_success(self):
        """测试验证成功"""
        config = MAConfig(periods=[10, 20, 30])
        config.validate()  # 不应该抛出异常

    def test_validate_not_list(self):
        """测试验证非列表"""
        config = MAConfig(periods="not_a_list")

        with pytest.raises(ValueError, match="periods must be a list"):
            config.validate()

    def test_validate_non_positive_periods(self):
        """测试验证非正周期"""
        config = MAConfig(periods=[10, -5, 30])

        with pytest.raises(ValueError, match="All periods must be positive integers"):
            config.validate()

    def test_validate_non_integer_periods(self):
        """测试验证非整数周期"""
        config = MAConfig(periods=[10, 20.5, 30])

        with pytest.raises(ValueError, match="All periods must be positive integers"):
            config.validate()

    def test_validate_duplicate_periods(self):
        """测试验证重复周期"""
        config = MAConfig(periods=[10, 20, 20])

        with pytest.raises(ValueError, match="Periods must be unique"):
            config.validate()


class TestRSIConfig:
    """测试RSI配置"""

    def test_default_values(self):
        """测试默认值"""
        config = RSIConfig()
        assert config.period == 14

    def test_custom_period(self):
        """测试自定义周期"""
        config = RSIConfig(period=20)
        assert config.period == 20

    def test_validate_success(self):
        """测试验证成功"""
        config = RSIConfig(period=14)
        config.validate()  # 不应该抛出异常

    def test_validate_non_positive_period(self):
        """测试验证非正周期"""
        config = RSIConfig(period=0)

        with pytest.raises(ValueError, match="period must be a positive integer"):
            config.validate()

    def test_validate_non_integer_period(self):
        """测试验证非整数周期"""
        config = RSIConfig(period=14.5)

        with pytest.raises(ValueError, match="period must be a positive integer"):
            config.validate()


class TestRSIStrategyConfig:
    """测试RSI策略配置"""

    def test_default_values(self):
        """测试默认值"""
        config = RSIStrategyConfig()

        assert config.oversold_threshold == 30
        assert config.overbought_threshold == 70
        assert config.lookback_period == 5
        assert isinstance(config.rsi_config, RSIConfig)

    def test_custom_values(self):
        """测试自定义值"""
        rsi_config = RSIConfig(period=20)
        config = RSIStrategyConfig(
            oversold_threshold=25,
            overbought_threshold=75,
            lookback_period=3,
            rsi_config=rsi_config,
        )

        assert config.oversold_threshold == 25
        assert config.overbought_threshold == 75
        assert config.lookback_period == 3
        assert config.rsi_config.period == 20

    def test_validate_success(self):
        """测试验证成功"""
        config = RSIStrategyConfig()
        config.validate()  # 不应该抛出异常

    def test_validate_invalid_thresholds(self):
        """测试验证无效阈值"""
        config = RSIStrategyConfig(oversold_threshold=70, overbought_threshold=30)

        with pytest.raises(
            ValueError,
            match="oversold_threshold must be less than overbought_threshold",
        ):
            config.validate()

    def test_validate_invalid_lookback_period(self):
        """测试验证无效回看期"""
        config = RSIStrategyConfig(lookback_period=0)

        with pytest.raises(
            ValueError, match="lookback_period must be a positive integer"
        ):
            config.validate()

    def test_validate_invalid_threshold_ranges(self):
        """测试验证无效阈值范围"""
        config = RSIStrategyConfig(oversold_threshold=-10, overbought_threshold=110)

        with pytest.raises(
            ValueError, match="oversold_threshold must be between 0 and 100"
        ):
            config.validate()

        config = RSIStrategyConfig(oversold_threshold=30, overbought_threshold=110)

        with pytest.raises(
            ValueError, match="overbought_threshold must be between 0 and 100"
        ):
            config.validate()


class TestMACrossStrategyConfig:
    """测试均线交叉策略配置"""

    def test_default_values(self):
        """测试默认值"""
        config = MACrossStrategyConfig()

        assert config.signal_threshold == 0.01
        assert isinstance(config.ma_config, MAConfig)

    def test_custom_values(self):
        """测试自定义值"""
        ma_config = MAConfig(periods=[10, 20])
        config = MACrossStrategyConfig(signal_threshold=0.02, ma_config=ma_config)

        assert config.signal_threshold == 0.02
        assert config.ma_config.periods == [10, 20]

    def test_validate_success(self):
        """测试验证成功"""
        config = MACrossStrategyConfig()
        config.validate()  # 不应该抛出异常

    def test_validate_invalid_signal_threshold(self):
        """测试验证无效信号阈值"""
        config = MACrossStrategyConfig(signal_threshold=0)

        with pytest.raises(
            ValueError, match="signal_threshold must be a positive number"
        ):
            config.validate()

    def test_validate_insufficient_periods(self):
        """测试验证周期不足"""
        ma_config = MAConfig(periods=[10])
        config = MACrossStrategyConfig(ma_config=ma_config)

        with pytest.raises(ValueError, match="MA strategy requires at least 2 periods"):
            config.validate()
