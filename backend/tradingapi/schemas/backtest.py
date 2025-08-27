from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from tradingapi.strategyv2.model import BacktestStats  # 官方驼峰生成器

from .stocks import StockBasicInfoFilter, StockCodeType
from .strategy import Strategy


class TradeType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


# 图表数据响应模型
class ChartData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    chart_date: datetime = Field(..., alias="date", description="K线日期")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: int = Field(..., description="成交量")

    # 新增字段存储未知列
    extra_fields: Dict[str, Any] = Field(
        default_factory=dict, description="动态存储的额外字段"
    )


# 单股回测响应模型
class BacktestResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        alias_generator=to_camel,
    )

    id: str = Field(..., description="回测 ID")
    stock_code: str = Field(..., alias="stockCode", description="股票代码")
    stock_name: str = Field(..., alias="stockName", description="股票名称")

    chart_data: List[ChartData] = Field(..., alias="chartData", description="图表数据")
    backtest_stats: BacktestStats = Field(
        ..., alias="backtestStats", description="回测统计"
    )

# 回测列表项
class BacktestListItem(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        alias_generator=to_camel,
    )
    id: str = Field(..., description="回测 ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    strategy: Dict = Field(..., description="策略参数")
    start: datetime = Field(..., description="开始时间")
    end: datetime = Field(..., description="结束时间")
    # status: str = Field(..., description="回测状态：completed / running / failed")


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
    strategy: Strategy = Field(..., description="策略配置")

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
    strategies: List[Strategy] = Field(..., description="策略配置列表")


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
