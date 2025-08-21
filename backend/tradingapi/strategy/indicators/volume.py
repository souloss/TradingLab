"""
成交量类指标
"""

import pandas as pd

from tradingapi.fetcher.interface import OHLCVExtendedSchema

from tradingapi.strategy.base import IndicatorCategory, IndicatorResult
from tradingapi.strategy.config import VolumeConfig
from tradingapi.strategy.indicators.base import IndicatorCalculator, register_indicator


@register_indicator("VOLUME")
class VolumeIndicator(IndicatorCalculator[VolumeConfig]):
    """成交量指标计算器"""

    @property
    def name(self) -> str:
        return "Volume"

    @property
    def category(self) -> IndicatorCategory:
        return IndicatorCategory.VOLUME

    def calculate(self, df: pd.DataFrame, config: VolumeConfig) -> IndicatorResult:
        """计算成交量指标"""
        if not self.validate_inputs(df):
            raise ValueError("Invalid input data for Volume calculation")

        volume = df[OHLCVExtendedSchema.volume]

        # 计算各期移动平均线
        result_dict = {"Volume": volume}
        for period in config.ma_periods:
            result_dict[f"Vol_MA{period}"] = volume.rolling(window=period).mean()

        result_df = pd.DataFrame(result_dict, index=df.index)

        return IndicatorResult(
            name=self.name, values=result_df, metadata=config.to_dict()
        )
