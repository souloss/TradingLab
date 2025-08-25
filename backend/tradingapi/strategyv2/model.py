from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class TradeRecord(BaseModel):
    size: int = Field(..., description="交易数量（股数或合约数）")
    entry_bar: int = Field(..., description="开仓所在的K线索引")
    exit_bar: int = Field(..., description="平仓所在的K线索引")
    entry_price: float = Field(..., description="开仓价格")
    exit_price: float = Field(..., description="平仓价格")
    sl: Optional[float] = Field(None, description="止损价（如果有）")
    tp: Optional[float] = Field(None, description="止盈价（如果有）")
    pnl: float = Field(..., description="盈亏金额 ($)")
    commission: float = Field(..., description="手续费 ($)")
    return_pct: float = Field(..., description="交易收益率 (%)")
    entry_time: datetime = Field(..., description="开仓时间")
    exit_time: datetime = Field(..., description="平仓时间")
    duration: timedelta = Field(..., description="交易持续时间")
    tag: Optional[str] = Field(None, description="交易标签（策略标记等）")

    # 额外字段统一收集
    extra: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")  # 允许额外字段

    def __init__(self, **data):
        # 提取额外字段
        base_fields = set(self.__class__.model_fields.keys())
        # 已经传入的 extra
        input_extra = data.pop("extra", {})
        # 计算动态字段
        extra_fields = {k: v for k, v in data.items() if k not in base_fields}
        # 合并
        data["extra"] = {**extra_fields, **input_extra}
        super().__init__(**data)


class EquityPoint(BaseModel):
    timestamp: datetime
    equity: float
    drawdown_pct: float
    drawdown_duration: Optional[str]


class BacktestStats(BaseModel):
    start: datetime = Field(..., description="回测开始时间")
    end: datetime = Field(..., description="回测结束时间")
    duration: timedelta = Field(..., description="回测持续时长")
    exposure_time_pct: float = Field(
        ..., description="建仓时间占比 (%)，反映资金利用率"
    )
    equity_final: float = Field(..., description="回测结束时的最终权益 ($)")
    equity_peak: float = Field(..., description="历史最高权益 ($)")
    commissions: float = Field(..., description="总手续费 ($)")
    return_pct: float = Field(..., description="总收益率 (%)")
    buy_hold_return_pct: float = Field(..., description="买入并持有的收益率 (%)")
    return_ann_pct: float = Field(..., description="年化收益率 (%)")
    volatility_ann_pct: float = Field(..., description="年化波动率 (%)")
    cagr_pct: float = Field(..., description="复合年化增长率 CAGR (%)")
    sharpe_ratio: float = Field(..., description="夏普比率 (风险调整收益)")
    sortino_ratio: float = Field(..., description="索提诺比率 (下行风险调整收益)")
    calmar_ratio: float = Field(..., description="卡玛比率 (收益与最大回撤比)")
    alpha_pct: float = Field(..., description="阿尔法 (超额收益率 %)")
    beta: float = Field(..., description="贝塔 (市场相关性系数)")
    max_drawdown_pct: float = Field(..., description="最大回撤 (%)")
    avg_drawdown_pct: float = Field(..., description="平均回撤 (%)")
    max_drawdown_duration: timedelta = Field(..., description="最大回撤持续时间")
    avg_drawdown_duration: timedelta = Field(..., description="平均回撤持续时间")
    n_trades: int = Field(..., description="交易次数")
    win_rate_pct: float = Field(..., description="胜率 (%)")
    best_trade_pct: float = Field(..., description="最佳单笔交易收益率 (%)")
    worst_trade_pct: float = Field(..., description="最差单笔交易收益率 (%)")
    avg_trade_pct: float = Field(..., description="平均单笔交易收益率 (%)")
    max_trade_duration: timedelta = Field(..., description="最长交易持续时间")
    avg_trade_duration: timedelta = Field(..., description="平均交易持续时间")
    profit_factor: Optional[float] = Field(None, description="利润因子 (总盈利/总亏损)")
    expectancy_pct: float = Field(
        ..., description="期望收益率 (%)，每笔交易的平均期望回报"
    )
    sqn: float = Field(..., description="系统质量数 SQN")
    kelly_criterion: Optional[float] = Field(None, description="凯利公式仓位比例")

    equity_curve: List[EquityPoint] = Field(..., description="账户权益数据")
    trades: List[TradeRecord] = Field(..., description="交易记录")
    strategy: Dict = Field(..., description="策略参数")


def convert_timestamps(obj):
    """
    递归将对象中的 pandas Timestamp 转为 datetime
    """
    if isinstance(obj, pd.Timestamp):
        return obj.to_pydatetime()
    elif isinstance(obj, list):
        return [convert_timestamps(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_timestamps(v) for k, v in obj.items()}
    elif hasattr(obj, "__dict__"):
        for k, v in list(obj.__dict__.items()):  # 转成 list 先复制 key-value
            setattr(obj, k, convert_timestamps(v))
        return obj
    else:
        return obj


def safe_get(stats: pd.Series, key: str, default: Any):
    """
    从 stats 中安全获取值，如果缺失或 NaN 返回默认值
    """
    value = stats.get(key, default)
    if pd.isna(value):
        return default
    return value


def safe_timedelta(value) -> timedelta:
    """
    安全将 stats 中的持续时间字段转换为 Python 的 `timedelta` 对象。
    支持输入类型包括：
    - None 或 NaN（返回 timedelta(0)）
    - Python 内置的 `datetime.timedelta`
    - Pandas 的 `pd.Timedelta`（含内部类型 `pandas._libs.tslibs.timedeltas.Timedelta`）
    - NumPy 的 `np.timedelta64`
    - 字符串（如 "5 days 00:00:00"）
    """
    if value is None or pd.isna(value) or value == "0":
        return timedelta(0)

    # 优先处理 Pandas 内部 Timedelta 类型
    if isinstance(value, pd.Timedelta):
        return value.to_pytimedelta()

    # 处理 Python 内置的 timedelta
    if isinstance(value, timedelta):
        return value

    try:
        # 处理 NumPy timedelta64 或字符串
        return pd.to_timedelta(value).to_pytimedelta()
    except Exception:
        return timedelta(0)


def parse_backtest_result(result) -> BacktestStats:
    """
    将 bt.run() 的结果序列化为 BacktestStats
    """
    stats = result  # pandas.Series
    trades_df: pd.DataFrame = stats.get("_trades", pd.DataFrame())
    equity_df: pd.DataFrame = stats.get("_equity_curve", pd.DataFrame())
    strategy = stats.get("_strategy")

    # 处理 trades
    trades = []
    for _, row in trades_df.iterrows():
        fixed = {
            "size": safe_get(row, "Size", 0),
            "entry_bar": safe_get(row, "EntryBar", 0),
            "exit_bar": safe_get(row, "ExitBar", 0),
            "entry_price": safe_get(row, "EntryPrice", 0.0),
            "exit_price": safe_get(row, "ExitPrice", 0.0),
            "pnl": safe_get(row, "PnL", 0.0),
            "commission": safe_get(row, "Commission", 0.0),
            "return_pct": safe_get(row, "ReturnPct", 0.0),
            "entry_time": safe_get(row, "EntryTime", None),
            "exit_time": safe_get(row, "ExitTime", None),
            "duration": str(safe_get(row, "Duration", timedelta(0))),
            "tag": safe_get(row, "Tag", None),
        }
        # 动态字段
        dynamic = {k: v for k, v in row.items() if k not in fixed}
        trades.append(TradeRecord(**fixed, extra=dynamic))

    # 处理 equity_curve
    equity_curve = []
    for ts, row in equity_df.iterrows():
        equity_curve.append(
            EquityPoint(
                timestamp=ts,
                equity=safe_get(row, "Equity", 0.0),
                drawdown_pct=safe_get(row, "DrawdownPct", 0.0),
                drawdown_duration=str(safe_get(row, "DrawdownDuration", timedelta(0))),
            )
        )

    # 构建 BacktestStats
    backtestStats = BacktestStats(
        start=safe_get(stats, "Start", datetime.now()),
        end=safe_get(stats, "End", datetime.now()),
        duration=safe_timedelta(safe_get(stats, "Duration", timedelta(0))),
        exposure_time_pct=safe_get(stats, "Exposure Time [%]", 0.0),
        equity_final=safe_get(stats, "Equity Final [$]", 0.0),
        equity_peak=safe_get(stats, "Equity Peak [$]", 0.0),
        commissions=safe_get(stats, "Commissions [$]", 0.0),
        return_pct=safe_get(stats, "Return [%]", 0.0),
        buy_hold_return_pct=safe_get(stats, "Buy & Hold Return [%]", 0.0),
        return_ann_pct=safe_get(stats, "Return (Ann.) [%]", 0.0),
        volatility_ann_pct=safe_get(stats, "Volatility (Ann.) [%]", 0.0),
        cagr_pct=safe_get(stats, "CAGR [%]", 0.0),
        sharpe_ratio=safe_get(stats, "Sharpe Ratio", 0.0),
        sortino_ratio=safe_get(stats, "Sortino Ratio", 0.0),
        calmar_ratio=safe_get(stats, "Calmar Ratio", 0.0),
        alpha_pct=safe_get(stats, "Alpha [%]", 0.0),
        beta=safe_get(stats, "Beta", 0.0),
        max_drawdown_pct=safe_get(stats, "Max. Drawdown [%]", 0.0),
        avg_drawdown_pct=safe_get(stats, "Avg. Drawdown [%]", 0.0),
        max_drawdown_duration=safe_timedelta(
            safe_get(stats, "Max. Drawdown Duration", timedelta(0))
        ),
        avg_drawdown_duration=safe_timedelta(
            safe_get(stats, "Avg. Drawdown Duration", timedelta(0))
        ),
        n_trades=safe_get(stats, "# Trades", 0),
        win_rate_pct=safe_get(stats, "Win Rate [%]", 0.0),
        best_trade_pct=safe_get(stats, "Best Trade [%]", 0.0),
        worst_trade_pct=safe_get(stats, "Worst Trade [%]", 0.0),
        avg_trade_pct=safe_get(stats, "Avg. Trade [%]", 0.0),
        max_trade_duration=safe_timedelta(
            safe_get(stats, "Max. Trade Duration", timedelta(0))
        ),
        avg_trade_duration=safe_timedelta(
            safe_get(stats, "Avg. Trade Duration", timedelta(0))
        ),
        profit_factor=safe_get(stats, "Profit Factor", None),
        expectancy_pct=safe_get(stats, "Expectancy [%]", 0.0),
        sqn=safe_get(stats, "SQN", 0.0),
        kelly_criterion=safe_get(stats, "Kelly Criterion", None),
        equity_curve=equity_curve,
        trades=trades,
        strategy=strategy.to_dict() if strategy else {},
    )

    return convert_timestamps(backtestStats)
