# models/stock_basic_info.py
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class StockBasicInfoBase(SQLModel):
    """股票基本信息基础模型"""

    exchange: str = Field(max_length=10, nullable=False)  # 交易所（SZ/SH/BJ）
    section: str = Field(max_length=20, nullable=False)  # 板块（主板/创业板/科创板等）
    stock_type: Optional[str] = Field(max_length=10)  # 股票类型（A股/B股/AB股等）
    name: str = Field(max_length=50, nullable=False)  # 名称
    listing_date: Optional[date] = Field(default=None)  # 上市时间
    industry: Optional[str] = Field(max_length=50)  # 行业
    total_shares: Optional[float] = Field(default=None)  # 总股本(股)
    float_shares: Optional[float] = Field(default=None)  # 流通股(股)
    total_market_value: Optional[float] = Field(default=None)  # 总市值(元)
    float_market_value: Optional[float] = Field(default=None)  # 流通市值(元)
    last_update: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now()),
    )  # 最后更新时间


class StockBasicInfo(StockBasicInfoBase, table=True):
    """股票基本信息表模型"""

    __tablename__ = "stock_basic_info"
    __table_args__ = {"extend_existing": True}

    symbol: str = Field(max_length=10, primary_key=True)  # 证券代码（主键）

    def __repr__(self):
        return f"<StockBasic(symbol='{self.symbol}', name='{self.name}')>"


class StockBasicInfoCreate(StockBasicInfoBase):
    """创建股票基本信息请求模型"""

    symbol: str = Field(max_length=10)  # 证券代码（主键）


class StockBasicInfoUpdate(SQLModel):
    """更新股票基本信息请求模型"""

    exchange: Optional[str] = Field(max_length=10)  # 交易所（SZ/SH/BJ）
    section: Optional[str] = Field(max_length=20)  # 板块（主板/创业板/科创板等）
    stock_type: Optional[str] = Field(max_length=10)  # 股票类型（A股/B股/AB股等）
    name: Optional[str] = Field(max_length=50)  # 名称
    listing_date: Optional[date]  # 上市时间
    industry: Optional[str] = Field(max_length=50)  # 行业
    total_shares: Optional[float]  # 总股本(股)
    float_shares: Optional[float]  # 流通股(股)
    total_market_value: Optional[float]  # 总市值(元)
    float_market_value: Optional[float]  # 流通市值(元)
