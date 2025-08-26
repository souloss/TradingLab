import datetime
from typing import Any, Callable, Dict, Union

import numpy as np
import pandas as pd
from backtesting import Strategy
from backtesting.lib import crossover
from talib import ATR, MA, MACD, SMA


def make_json_safe(value):
    """递归转换成 JSON 可序列化的对象"""
    if isinstance(value, (np.integer,)):
        return int(value)
    elif isinstance(value, (np.floating,)):
        return float(value)
    elif isinstance(value, (np.ndarray,)):
        return value.tolist()
    elif isinstance(value, datetime.datetime):
        return value.isoformat()
    elif isinstance(value, datetime.timedelta):
        return value.total_seconds()
    elif isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple, set)):
        return [make_json_safe(v) for v in value]
    else:
        return value


def crossunder(a, b):
    """Return True if series2 just crossed over (above) series1."""
    return crossover(b, a)


class BaseSerializableStrategy(Strategy):
    """
    通用可序列化策略基类
    - 自动收集策略参数
    - 自动捕获 self.I() 的技术指标
    """

    def init(self):
        # 用户策略的 init() 会覆盖这里
        super().init()

    def I(self, func, *args, name=None, **kwargs):
        """
        包装 backtesting.Strategy.I:
        - 保持原有功能
        - 自动捕获指标，记录到 _registered_indicators
        """
        value = super().I(func, *args, **kwargs)
        if not hasattr(self, "_registered_indicators"):
            self._registered_indicators = {}

        # 生成指标名字
        if name is None:
            base_name = func.__name__
            idx = len(
                [k for k in self._registered_indicators if k.startswith(base_name)]
            )
            name = f"{base_name}_{idx}" if idx else base_name

        self._registered_indicators[name] = value
        return value

    def to_dict(self):
        return {
            "name": self.__class__.__name__,
            "doc": self.__class__.__doc__,
            "params": make_json_safe(self._params) if self._params else {},
        }

    @classmethod
    def constraint(cls) -> Callable[[Any], bool]:
        """
        基类约束函数，子类应覆盖此方法
        """

        def constraint_func(param):
            # 默认情况下，接受所有参数组合
            return True

        return constraint_func


class MACDStrategy(BaseSerializableStrategy):
    """
    ## MACD指标交叉策略

    通过快速EMA与慢速EMA的差值(DIF)和信号线(DEA)的交叉关系生成交易信号。
    当DIF从下向上突破DEA时产生买入信号，当DIF从上向下跌破DEA时产生卖出信号。

    参数:
        fast_period: 快速EMA周期，默认12(日)
        slow_period: 慢速EMA周期，默认26(日)
        signal_period: 信号线周期，默认9(日)

    买卖逻辑:
        买入条件:
            - DIF上穿DEA(金叉)且当前无持仓
        卖出条件:
            - DIF下穿DEA(死叉)且当前有持仓
    """

    fast_period = 12
    slow_period = 26
    signal_period = 9

    def init(self):
        close = pd.Series(self.data.Close)
        self.dif, self.dea, self.hist = self.I(
            MACD, close, self.fast_period, self.slow_period, self.signal_period
        )

    def next(self):
        if crossover(self.dif, self.dea):
            if not self.position:
                self.buy()
        elif crossunder(self.dif, self.dea):
            if self.position:
                self.position.close()

    @classmethod
    def constraint(cls) -> Callable[[Any], bool]:
        """
        MACD策略的约束函数
        """

        def constraint_func(param):
            # 确保快速EMA < 慢速EMA，信号线周期 < 快速EMA
            return (
                param.fast_period < param.slow_period
                and param.signal_period < param.fast_period
            )

        return constraint_func

    @classmethod
    def optimization_space(cls) -> Dict[str, Union[range, list]]:
        """返回参数优化空间字典，使用range或列表代替np.ndarray"""
        return {
            "fast_period": range(5, 30, 5),  # 快速EMA周期范围
            "slow_period": range(20, 60, 5),  # 慢速EMA周期范围
            "signal_period": range(5, 15, 5),  # 信号线周期范围
        }


class MAStrategy(BaseSerializableStrategy):
    """
    双均线交叉策略

    通过短期均线与长期均线的交叉关系生成交易信号。
    当短期均线从下向上穿过长期均线时产生买入信号，
    当短期均线从上向下穿过长期均线时产生卖出信号。

    参数:
        short_period: 短期均线周期，默认10(日)
        long_period: 长期均线周期，默认30(日)

    买卖逻辑:
        买入条件:
            - 短期均线上穿长期均线(金叉)且当前无持仓
        卖出条件:
            - 短期均线下穿长期均线(死叉)且当前有持仓
    """

    short_period = 10  # 短期均线
    long_period = 30  # 长期均线

    def init(self):
        close = pd.Series(self.data.Close)
        self.short_period_ma = self.I(MA, close, self.short_period)
        self.long_period_ma = self.I(MA, close, self.long_period)

    def next(self):
        if crossover(self.short_period_ma, self.long_period_ma):
            if not self.position:  # 满足条件且没有持仓，买入
                self.buy()
        elif crossunder(self.short_period_ma, self.long_period_ma):
            if self.position:  # 满足条件且有持仓，卖出
                self.position.close()

    @classmethod
    def constraint(cls) -> Callable[[Any], bool]:
        """
        双均线策略的约束函数
        """

        def constraint_func(param):
            # 确保短期均线 < 长期均线
            return param.short_period < param.long_period

        return constraint_func

    @classmethod
    def optimization_space(cls) -> Dict[str, Union[range, list]]:
        """返回参数优化空间字典，使用range或列表代替np.ndarray"""
        return {
            "short_period": range(5, 40, 5),  # 短期均线周期范围
            "long_period": range(20, 120, 10),  # 长期均线周期范围
        }


class VolumeSpikeStrategy(BaseSerializableStrategy):
    """
    量价极端行情策略

    通过识别成交量极端情况和价格极值来捕捉反转机会。
    在地量地价时买入，在天量天价时卖出。

    参数:
        period: 回溯周期，用于计算成交量均线和价格极值，默认60(日)
        sell_volume_multiplier: 天量倍数阈值，默认3.0(成交量是均量的3倍)
        buy_volume_multiplier: 地量倍数阈值，默认0.4(成交量是均量的0.4倍)

    买卖逻辑:
        买入条件:
            - 成交量低于均量的一定比例(地量)
            - 价格处于近期最低点附近(地价)
            - 当前无持仓
        卖出条件:
            - 成交量高于均量的一定比例(天量)
            - 价格处于近期最高点附近(天价)
            - 当前有持仓
    """

    period = 60
    sell_volume_multiplier = 3.0
    buy_volume_multiplier = 0.4

    def init(self):
        # 成交量均线
        self.vol_ma = self.I(SMA, self.data.Volume.astype(float), self.period)

    def next(self):
        price = self.data.Close[-1]
        vol = self.data.Volume[-1]
        vol_ma = self.vol_ma[-1]

        # 计算价格极值
        price_min = self.data.Close[-self.period :].min()
        price_max = self.data.Close[-self.period :].max()

        # 买入条件：地量地价且当前没有持仓
        if (
            not self.position
            and vol < vol_ma * self.buy_volume_multiplier
            and price <= price_min * 1.05
        ):
            self.buy()  # 全仓买入

        # 卖出条件：天量天价且当前持仓
        elif (
            self.position
            and vol > vol_ma * self.sell_volume_multiplier
            and price >= price_max * 0.95
        ):
            self.position.close()  # 全仓卖出

    @classmethod
    def constraint(cls) -> Callable[[Any], bool]:
        """
        量价极端策略的约束函数
        """

        def constraint_func(param):
            # 确保高倍数 > 低倍数
            return param.sell_volume_multiplier > param.buy_volume_multiplier

        return constraint_func

    @classmethod
    def optimization_space(cls) -> Dict[str, Union[range, list]]:
        """返回参数优化空间字典，使用range或列表代替np.ndarray"""
        # 对于浮点数参数，使用列表代替np.arange
        return {
            "period": range(20, 120, 5),  # 回溯周期范围
            "sell_volume_multiplier": [
                round(x, 1) for x in np.arange(1.5, 6.0, 0.5)
            ],  # 天量倍数阈值范围
            "buy_volume_multiplier": [
                round(x, 2) for x in np.arange(0.2, 0.9, 0.1)
            ],  # 地量倍数阈值范围
        }


class ATRMeanReversionStrategy(BaseSerializableStrategy):
    """
    基于ATR的均值回归策略

    利用价格相对于均线的偏离程度和ATR波动率指标来判断超买超卖状态。
    当价格显著低于均线时买入，当价格显著高于均线时卖出。

    参数:
        period: 均价计算周期，默认20(日)
        atr_period: ATR计算周期，默认14(日)
        atr_multiplier: 波动率乘数，默认1.5(用于确定偏离阈值)

    买卖逻辑:
        买入条件:
            - 价格低于均线减去ATR的一定倍数(超卖区域)且当前无持仓
        卖出条件:
            - 价格高于均线加上ATR的一定倍数(超买区域)且当前有持仓
    """

    period = 20  # 均线周期
    atr_period = 14  # ATR 周期
    atr_multiplier = 1.5  # 偏离倍数

    def init(self):
        high, low, close = self.data.High, self.data.Low, self.data.Close
        self.ma = self.I(MA, close, self.period)
        self.atr = self.I(ATR, high, low, close, self.atr_period)

    def next(self):
        price = self.data.Close[-1]
        ma = self.ma[-1]
        atr = self.atr[-1]

        if price < ma - self.atr_multiplier * atr:
            if not self.position:  # 低估 → 买入
                self.buy()
        elif price > ma + self.atr_multiplier * atr:
            if self.position:  # 高估 → 平仓
                self.position.close()

    @classmethod
    def constraint(cls) -> Callable[[Any], bool]:
        """
        ATR均值回归策略的约束函数
        """

        def constraint_func(param):
            # 确保ATR周期 < 均线周期
            return param.atr_period < param.period

        return constraint_func

    @classmethod
    def optimization_space(cls) -> Dict[str, Union[range, list]]:
        """返回参数优化空间字典，使用range或列表代替np.ndarray"""
        # 对于浮点数参数，使用列表代替np.arange
        return {
            "period": range(10, 60, 3),  # 均线周期范围
            "atr_period": range(5, 30, 5),  # ATR周期范围
            "atr_multiplier": [
                round(x, 1) for x in np.arange(0.3, 6.0, 0.6)
            ],  # 波动率乘数范围
        }


StrategyMap = {
    "MACD": MACDStrategy,
    "MA": MAStrategy,
    "ATR": ATRMeanReversionStrategy,
    "VOLUME": VolumeSpikeStrategy,
}
