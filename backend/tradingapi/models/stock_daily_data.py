from datetime import date, datetime
from typing import Optional, Sequence

from sqlalchemy import Column, DateTime, UniqueConstraint, func
from sqlmodel import Field, SQLModel


class StockDailyDataBase(SQLModel):
    """股票每日数据基础模型"""

    symbol: str = Field(max_length=10, nullable=False)  # 股票代码
    trade_date: date = Field(nullable=False)  # 交易日期
    open_price: Optional[float] = Field(default=None)  # 开盘价
    close_price: Optional[float] = Field(default=None)  # 收盘价
    high_price: Optional[float] = Field(default=None)  # 最高价
    low_price: Optional[float] = Field(default=None)  # 最低价
    volume: Optional[float] = Field(default=None)  # 成交量(股)
    turnover: Optional[float] = Field(default=None)  # 成交额(元)
    amplitude: Optional[float] = Field(default=None)  # 振幅(%)
    change_rate: Optional[float] = Field(default=None)  # 涨跌幅(%)
    change_amount: Optional[float] = Field(default=None)  # 涨跌额
    turnover_rate: Optional[float] = Field(default=None)  # 换手率(%)
    last_update: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now()),
    )  # 最后更新时间


class StockDailyData(StockDailyDataBase, table=True):
    """股票每日数据表模型"""

    __tablename__ = "stock_daily_data"
    __table_args__ = (
        UniqueConstraint("symbol", "trade_date", name="uix_symbol_trade_date"),
        {"extend_existing": True},
    )

    id: Optional[int] = Field(default=None, primary_key=True)  # 主键ID

    def __repr__(self):
        return f"<DailyData(symbol='{self.symbol}', date={self.trade_date}, close={self.close_price})>"


class StockDailyDataCreate(StockDailyDataBase):
    """创建股票每日数据请求模型"""

    pass


class StockDailyDataUpdate(SQLModel):
    """更新股票每日数据请求模型"""

    open_price: Optional[float]  # 开盘价
    close_price: Optional[float]  # 收盘价
    high_price: Optional[float]  # 最高价
    low_price: Optional[float]  # 最低价
    volume: Optional[float]  # 成交量(股)
    turnover: Optional[float]  # 成交额(元)
    amplitude: Optional[float]  # 振幅(%)
    change_rate: Optional[float]  # 涨跌幅(%)
    change_amount: Optional[float]  # 涨跌额
    turnover_rate: Optional[float]  # 换手率(%)
