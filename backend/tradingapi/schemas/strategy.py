from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, Tag, model_validator
from pydantic.alias_generators import to_camel  # 官方驼峰生成器

from tradingapi.strategy.config.strategies import (ATRBreakoutStrategyConfig,
                                                   ATRConfig, MACDConfig,
                                                   MACDStrategyConfig,
                                                   MAConfig,
                                                   MACrossStrategyConfig,
                                                   VolumeSpikeStrategyConfig)


# ===== 策略参数模型 =====
class MACDParameters(BaseModel):
    """MACD指标参数配置"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    fast_period: int = Field(
        default=12,
        ge=1,
        le=100,
        description="快速EMA周期，范围[1,100]",
        json_schema_extra={"examples": [12]},
    )
    slow_period: int = Field(
        default=26,
        ge=1,
        le=100,
        description="慢速EMA周期，需大于fastPeriod",
        json_schema_extra={"examples": [26]},
    )
    signal_period: int = Field(
        default=9,
        ge=1,
        le=100,
        description="信号线周期",
        json_schema_extra={"examples": [9]},
    )

    @model_validator(mode="after")
    def validate_periods(self) -> "MACDParameters":
        """验证周期参数逻辑关系"""
        if self.slow_period <= self.fast_period:
            raise ValueError("slow_period 必须大于 fast_period")
        return self

    def technical_indicators_params(self) -> dict:
        return {
            "MACD_FAST": self.fast_period,
            "MACD_SLOW": self.slow_period,
            "MACD_SIGNAL": self.signal_period,
        }

    def to_strategies_config(self) -> MACDStrategyConfig:
        return MACDStrategyConfig(
            macd_config=MACDConfig(
                fast_period=self.fast_period,
                slow_period=self.slow_period,
                signal_period=self.signal_period,
            )
        )


class MAParameters(BaseModel):
    """移动平均线参数配置"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    short_period: int = Field(
        default=5,
        ge=1,
        le=100,
        description="短期均线周期",
        json_schema_extra={"examples": [5]},
    )
    long_period: int = Field(
        default=20,
        ge=1,
        le=100,
        description="长期均线周期，需大于shortPeriod",
        json_schema_extra={"examples": [20]},
    )

    @model_validator(mode="after")
    def validate_periods(self) -> "MAParameters":
        """验证长短周期逻辑关系"""
        if self.long_period <= self.short_period:
            raise ValueError("longPeriod必须大于shortPeriod")
        return self

    def to_strategies_config(self) -> MACrossStrategyConfig:
        return MACrossStrategyConfig(
            ma_config=MAConfig([self.short_period, self.long_period])
        )


class ATRParameters(BaseModel):
    """ATR波动率参数配置"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    atr_period: int = Field(
        default=14,
        ge=1,
        le=100,
        description="ATR计算周期",
        json_schema_extra={"examples": [14]},
    )
    high_low_period: int = Field(
        default=20,
        ge=1,
        le=100,
        description="高低价计算周期",
        json_schema_extra={"examples": [20]},
    )
    atr_multiplier: float = Field(
        default=1.5,
        ge=0.1,
        le=10.0,
        description="ATR波动乘数",
        json_schema_extra={"examples": [1.5]},
    )

    def to_strategies_config(self) -> ATRBreakoutStrategyConfig:
        return ATRBreakoutStrategyConfig(
            breakout_period=self.high_low_period,
            atr_multiplier=self.atr_multiplier,
            atr_config=ATRConfig(period=self.atr_period),
        )


class VolumeParameters(BaseModel):
    """成交量策略参数配置"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    time_range: int = Field(
        default=20,
        ge=1,
        le=100,
        description="成交量统计周期",
        json_schema_extra={"examples": [20]},
    )
    buy_volume_multiplier: float = Field(
        default=0.3,
        ge=0.1,
        le=5.0,
        description="买入成交量阈值乘数",
        json_schema_extra={"examples": [0.3]},
    )
    sell_volume_multiplier: float = Field(
        default=3.0,
        ge=1.0,
        le=10.0,
        description="卖出成交量阈值乘数",
        json_schema_extra={"examples": [3.0]},
    )

    def to_strategies_config(self) -> VolumeSpikeStrategyConfig:
        return VolumeSpikeStrategyConfig(
            high_multiplier=self.sell_volume_multiplier,
            low_multiplier=self.buy_volume_multiplier,
            period=self.time_range,
        )


# ===== 统一策略模型 =====
class StrategyItem(BaseModel):
    """策略配置基类"""

    type: Literal["MACD", "MA", "ATR", "VOLUME"] = Field(
        ..., description="策略类型标识", json_schema_extra={"examples": ["MACD"]}
    )
    parameters: Union[
        Annotated[MACDParameters, Tag("MACD")],
        Annotated[MAParameters, Tag("MA")],
        Annotated[ATRParameters, Tag("ATR")],
        Annotated[VolumeParameters, Tag("VOLUME")],
    ] = Field(..., description="策略具体参数配置")
