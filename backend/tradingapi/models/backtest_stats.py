import math
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4
from sqlmodel import SQLModel, Field, Column, JSON
from pydantic import TypeAdapter
from fastapi.encoders import jsonable_encoder

from tradingapi.strategyv2.model import BacktestStats, EquityPoint, TradeRecord


# ---------- JSON 安全序列化 ----------


def make_json_safe(obj: Any) -> Any:
    """扩展版 jsonable_encoder，支持 timedelta 和 NaN/Inf 值"""

    def replace_special_values(value: Any) -> Any:
        """递归替换特殊值（NaN、Inf、timedelta）"""
        if isinstance(value, dict):
            return {k: replace_special_values(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [replace_special_values(item) for item in value]
        elif isinstance(value, timedelta):
            return value.total_seconds()
        elif isinstance(value, float):
            if math.isnan(value):
                return None  # 将 NaN 替换为 None
            elif math.isinf(value):
                return None if value > 0 else None  # 将 ±Inf 替换为 None
            return value
        # 处理 NumPy 类型（如果安装了 NumPy）
        try:
            import numpy as np

            if isinstance(value, (np.floating, np.integer)):
                if np.isnan(value):
                    return None
                elif np.isinf(value):
                    return None
                return value.item()  # 转换为 Python 原生类型
        except ImportError:
            pass
        return value

    # 先使用 FastAPI 的 jsonable_encoder 处理基本类型
    encoded = jsonable_encoder(obj)
    # 然后递归处理特殊值
    return replace_special_values(encoded)


class BacktestStatsTable(SQLModel, table=True):
    __tablename__ = "backtest_stats"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)

    # 基础字段
    start: datetime
    end: datetime
    duration_seconds: int = Field(..., description="回测持续时长（秒）")
    stock_code: str = Field(max_length=10, nullable=False)
    stock_name: str = Field(max_length=50, nullable=False)
    chart_data: List[Dict[str, Any]] = Field(sa_column=Column(JSON, nullable=False))

    exposure_time_pct: float
    equity_final: float
    equity_peak: float
    commissions: float
    return_pct: float
    buy_hold_return_pct: float
    return_ann_pct: float
    volatility_ann_pct: float
    cagr_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    alpha_pct: float
    beta: float
    max_drawdown_pct: float
    avg_drawdown_pct: float
    max_drawdown_duration_seconds: int
    avg_drawdown_duration_seconds: int
    n_trades: int
    win_rate_pct: float
    best_trade_pct: float
    worst_trade_pct: float
    avg_trade_pct: float
    max_trade_duration_seconds: int
    avg_trade_duration_seconds: int
    profit_factor: Optional[float] = None
    expectancy_pct: float
    sqn: Optional[float] = None
    kelly_criterion: Optional[float] = None

    # 复杂结构：用 JSON 存储
    equity_curve: List[Dict[str, Any]] = Field(sa_column=Column(JSON))
    trades: List[Dict[str, Any]] = Field(sa_column=Column(JSON))
    strategy: Dict[str, Any] = Field(sa_column=Column(JSON))

    # ============ 转换方法 ============

    @classmethod
    def from_pydantic(cls, stock_code, stock_name, chart_data, stats: BacktestStats) -> "BacktestStatsTable":
        data = stats.model_dump()

        return cls(
            stock_name=stock_name,
            stock_code=stock_code,
            chart_data = make_json_safe(chart_data),
            start=data["start"],
            end=data["end"],
            duration_seconds=data["duration"].total_seconds(),
            exposure_time_pct=data["exposure_time_pct"],
            equity_final=data["equity_final"],
            equity_peak=data["equity_peak"],
            commissions=data["commissions"],
            return_pct=data["return_pct"],
            buy_hold_return_pct=data["buy_hold_return_pct"],
            return_ann_pct=data["return_ann_pct"],
            volatility_ann_pct=data["volatility_ann_pct"],
            cagr_pct=data["cagr_pct"],
            sharpe_ratio=data["sharpe_ratio"],
            sortino_ratio=data["sortino_ratio"],
            calmar_ratio=data["calmar_ratio"],
            alpha_pct=data["alpha_pct"],
            beta=data["beta"],
            max_drawdown_pct=data["max_drawdown_pct"],
            avg_drawdown_pct=data["avg_drawdown_pct"],
            max_drawdown_duration_seconds=data["max_drawdown_duration"].total_seconds(),
            avg_drawdown_duration_seconds=data["avg_drawdown_duration"].total_seconds(),
            n_trades=data["n_trades"],
            win_rate_pct=data["win_rate_pct"],
            best_trade_pct=data["best_trade_pct"],
            worst_trade_pct=data["worst_trade_pct"],
            avg_trade_pct=data["avg_trade_pct"],
            max_trade_duration_seconds=data["max_trade_duration"].total_seconds(),
            avg_trade_duration_seconds=data["avg_trade_duration"].total_seconds(),
            profit_factor=data["profit_factor"],
            expectancy_pct=data["expectancy_pct"],
            sqn=data["sqn"],
            kelly_criterion=data["kelly_criterion"],
            # 🚨 关键：把 Pydantic 模型转成 JSON-safe dict/list
            equity_curve=[make_json_safe(ep) for ep in stats.equity_curve],
            trades=[make_json_safe(tr) for tr in stats.trades],
            strategy=make_json_safe(stats.strategy),
        )

    def to_pydantic(self) -> BacktestStats:
        return BacktestStats(
            start=self.start,
            end=self.end,
            duration=timedelta(seconds=self.duration_seconds),
            exposure_time_pct=self.exposure_time_pct,
            equity_final=self.equity_final,
            equity_peak=self.equity_peak,
            commissions=self.commissions,
            return_pct=self.return_pct,
            buy_hold_return_pct=self.buy_hold_return_pct,
            return_ann_pct=self.return_ann_pct,
            volatility_ann_pct=self.volatility_ann_pct,
            cagr_pct=self.cagr_pct,
            sharpe_ratio=self.sharpe_ratio,
            sortino_ratio=self.sortino_ratio,
            calmar_ratio=self.calmar_ratio,
            alpha_pct=self.alpha_pct,
            beta=self.beta,
            max_drawdown_pct=self.max_drawdown_pct,
            avg_drawdown_pct=self.avg_drawdown_pct,
            max_drawdown_duration=timedelta(seconds=self.max_drawdown_duration_seconds),
            avg_drawdown_duration=timedelta(seconds=self.avg_drawdown_duration_seconds),
            n_trades=self.n_trades,
            win_rate_pct=self.win_rate_pct,
            best_trade_pct=self.best_trade_pct,
            worst_trade_pct=self.worst_trade_pct,
            avg_trade_pct=self.avg_trade_pct,
            max_trade_duration=timedelta(seconds=self.max_trade_duration_seconds),
            avg_trade_duration=timedelta(seconds=self.avg_trade_duration_seconds),
            profit_factor=self.profit_factor,
            expectancy_pct=self.expectancy_pct,
            sqn = self.sqn if self.sqn is not None else 0.0,
            kelly_criterion=self.kelly_criterion,
            # 🚨 把 JSON dict 转回 Pydantic 模型
            equity_curve=[EquityPoint(**ep) for ep in self.equity_curve],
            trades=[TradeRecord(**tr) for tr in self.trades],
            strategy=self.strategy,
        )
