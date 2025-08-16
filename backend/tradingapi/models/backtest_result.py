from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, func
from sqlmodel import Field, SQLModel


class BacktestResultBase(SQLModel):
    """回测结果基础模型"""

    stock_code: str = Field(max_length=10, nullable=False)
    stock_name: str = Field(max_length=50, nullable=False)
    start_date: datetime = Field(nullable=False)
    end_date: datetime = Field(nullable=False)
    strategies: Dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    stock_return: float = Field(nullable=False)
    trade_count: int = Field(nullable=False)
    trades: List[Dict[str, Any]] = Field(sa_column=Column(JSON, nullable=False))
    chart_data: List[Dict[str, Any]] = Field(sa_column=Column(JSON, nullable=False))
    last_update: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now()),
    )


class BacktestResult(BacktestResultBase, table=True):
    """回测结果表模型"""

    __tablename__ = "backtest_results"
    __table_args__ = {"extend_existing": True}

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class BacktestResultCreate(BacktestResultBase):
    """创建回测结果请求模型"""

    pass


class BacktestResultUpdate(SQLModel):
    """更新回测结果请求模型"""

    stock_code: Optional[str] = Field(max_length=10)
    stock_name: Optional[str] = Field(max_length=50)
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    strategies: Optional[Dict[str, Any]]
    stock_return: Optional[float]
    trade_count: Optional[int]
    trades: Optional[List[Dict[str, Any]]]
    chart_data: Optional[List[Dict[str, Any]]]
