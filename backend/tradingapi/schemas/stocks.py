from datetime import date, datetime
from typing import Annotated, List, Optional

from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel  # 官方驼峰生成器


def validate_stock_code(code: str) -> str:
    if not code.isdigit() or len(code) != 6:
        raise ValueError("股票代码必须为6位数字")
    return code


StockCodeType = Annotated[str, AfterValidator(validate_stock_code)]


# 基础响应模型（包含所有字段）
class StockBasicInfoSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, from_attributes=True, populate_by_name=True
    )

    symbol: str = Field(
        ..., alias="symbol", description="证券代码", examples=["600000"]
    )
    name: str = Field(..., description="名称", examples=["浦发银行"])
    exchange: str = Field(..., description="交易所", examples=["SH"])
    section: str = Field(..., description="板块", examples=["主板"])
    stock_type: Optional[str] = Field(None, description="股票类型", examples=["A股"])
    listing_date: Optional[date] = Field(
        None, description="上市时间", examples=["1999-11-10"]
    )
    industry: Optional[str] = Field(None, description="行业", examples=["银行"])
    total_shares: Optional[float] = Field(
        None, description="总股本(股)", examples=[293.52]
    )
    float_shares: Optional[float] = Field(
        None, description="流通股(股)", examples=[293.52]
    )
    total_market_value: Optional[float] = Field(
        None, description="总市值(元)", examples=[2150.23]
    )
    float_market_value: Optional[float] = Field(
        None, description="流通市值(元)", examples=[2150.23]
    )
    last_update: datetime = Field(..., description="最后更新时间")


# 精简响应模型（排除敏感/大字段）
class StockBasicInfoLiteSchema(BaseModel):
    symbol: str = Field(..., description="证券代码")
    name: str = Field(..., description="名称")
    exchange: str = Field(..., description="交易所")
    section: str = Field(..., description="板块")
    industry: Optional[str] = Field(None, description="行业")


# 股票过滤器请求模型
class StockBasicInfoFilter(BaseModel):
    exchange: Optional[List[str]] = Field(
        None, description="交易所过滤(SH/SZ/BJ)", examples=[["SH", "SZ"]]
    )
    sections: Optional[List[str]] = Field(
        None,
        description="板块过滤(主板/创业板/科创板等)",
        examples=[["主板", "创业板"]],
    )
    stock_type: Optional[List[str]] = Field(
        None, description="股票类型过滤(A股/B股等)", examples=[["A股", "B股"]]
    )
    industries: Optional[List[str]] = Field(
        None, description="行业过滤", examples=[["银行", "医药"]]
    )
    start_listing_date: Optional[date] = Field(
        None, description="最小上市日期", examples=["2020-01-01"]
    )
    end_listing_date: Optional[date] = Field(
        None, description="最大上市日期", examples=["2023-12-31"]
    )
    min_market_cap: Optional[float] = Field(
        None, description="最小流通市值(元)", examples=[50]
    )
    max_market_cap: Optional[float] = Field(
        None, description="最大流通市值(元)", examples=[200000000000]
    )
