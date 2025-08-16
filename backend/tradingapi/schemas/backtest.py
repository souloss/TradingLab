import json
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import (BaseModel, ConfigDict, Field, field_validator,
                      model_validator)
from pydantic.alias_generators import to_camel  # 官方驼峰生成器

from .stocks import StockBasicInfoFilter, StockCodeType
from .strategy import StrategyItem


class TradeType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


# 交易记录响应模型
class Trade(BaseModel):
    model_config = ConfigDict(populate_by_name=True)  # 允许使用原始名称或别名

    trade_date: datetime = Field(..., alias="date", description="交易日期")
    type: TradeType = Field(
        ..., description="交易类型", json_schema_extra={"examples": ["BUY"]}
    )
    price: float = Field(..., description="交易价格")
    quantity: int = Field(..., description="交易数量")
    commission: float = Field(..., description="交易佣金")
    marketValue: float = Field(..., description="交易后市值")
    cashBalance: float = Field(..., description="交易后现金余额")


# 图表数据响应模型
class ChartData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)  # 允许使用原始名称或别名

    chart_date: datetime = Field(..., alias="date", description="K线日期")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量")


# 单股回测响应模型
class BacktestResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str = Field(..., description="回测 ID")
    stock_code: str = Field(..., alias="stockCode", description="股票代码")
    stock_name: str = Field(..., alias="stockName", description="股票名称")
    stock_return: float = Field(..., alias="return", description="收益率")
    trade_count: int = Field(..., alias="tradeCount", description="交易次数")
    trades: List[Trade] = Field(..., description="交易记录")
    chart_data: List[ChartData] = Field(..., alias="chartData", description="图表数据")
    strategies: List[StrategyItem] = Field(..., description="策略配置列表")

    @field_validator("trades", "chart_data", "strategies", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


# 单股回测请求模型
class BacktestRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    stock_code: StockCodeType = Field(
        ..., description="6位数字股票代码", examples=["000001"]
    )
    start_date: date = Field(
        ..., description="回测开始日期（YYYY-MM-DD）", examples=["2024-08-10"]
    )
    end_date: date = Field(
        ..., description="回测结束日期（YYYY-MM-DD）", examples=["2025-08-10"]
    )
    strategies: List[StrategyItem] = Field(
        ..., min_length=1, description="策略配置列表"
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "BacktestRequest":
        if self.start_date >= self.end_date:
            raise ValueError("开始日期必须早于结束日期")
        return self


# 选股回测响应模型
class BacktestResultItem(BaseModel):
    """单股回测结果项"""

    stock_code: str = Field(..., alias="stockCode", description="股票代码")
    backtest_id: str = Field(..., alias="backtestId", description="回测ID")
    stock_return: float = Field(..., alias="return", description="收益率")
    signal_type: Literal["BUY", "SELL", "HOLD"] = Field(
        ..., alias="signalType", description="交易信号类型"
    )
    buy_count: int = Field(..., alias="buyCount", description="买入次数")
    sell_count: int = Field(..., alias="sellCount", description="卖出次数")

    class Config:
        """配置类"""

        populate_by_name = True  # 允许使用字段别名
        from_attributes = True  # 允许从属性创建模型


BacktestResults = List[BacktestResultItem]


# 选股请求模型
class SelectStockBacktestReq(BaseModel):
    filter: StockBasicInfoFilter = Field(
        None,
        description="股票高级过滤器",
    )
    strategies: List[StrategyItem] = Field(
        ..., min_length=1, description="策略配置列表"
    )


class StockResult(BaseModel):
    stock_code: str = Field(..., alias="stockCode", description="股票代码")
    stock_name: str = Field(..., alias="stockName", description="股票名称")
    industry: str = Field(..., description="行业")
    signal_type: str = Field(..., alias="signalType", description="信号类型")
    annual_return: float = Field(..., alias="annualReturn", description="年化收益率")
    market_cap: float = Field(..., alias="marketCap", description="市值")

    model_config = ConfigDict(populate_by_name=True)


# 选股响应模型
class SelectStockBacktestRsp(BaseModel):
    id: str = Field(..., description="唯一标识符")
    stock_count: int = Field(..., alias="stockCount", description="股票数量")
    buy_signals: int = Field(..., alias="buySignals", description="买入信号数量")
    sell_signals: int = Field(..., alias="sellSignals", description="卖出信号数量")
    average_return: float = Field(..., alias="averageReturn", description="平均收益率")
    results: List[StockResult] = Field(..., description="股票结果列表")

    model_config = ConfigDict(populate_by_name=True)
