from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class StockIndustryBase(SQLModel):
    industry_code: str = Field(max_length=20, unique=True, nullable=False)  # 行业代码
    name: str = Field(max_length=50, unique=True, nullable=False)  # 行业名称
    level: int = Field(default=1)  # 行业级别(1-一级行业, 2-二级行业)
    parent_code: Optional[str] = Field(
        default=None, foreign_key="stock_industry.industry_code", max_length=20
    )  # 上级行业代码
    component_count: Optional[int] = None  # 成份个数
    pe_ratio: Optional[float] = None  # 静态市盈率
    pe_ratio_ttm: Optional[float] = None  # TTM(滚动)市盈率
    pb_ratio: Optional[float] = None  # 市净率
    dividend_yield: Optional[float] = None  # 静态股息率


class StockIndustry(StockIndustryBase, table=True):
    """行业分类表"""

    __tablename__ = "stock_industry"

    id: Optional[int] = Field(default=None, primary_key=True)
    last_update: datetime = Field(
        default_factory=datetime.now(timezone.utc)
    )  # 最后更新时间

    # 修改后的关系定义
    parent: Optional["StockIndustry"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs=dict(
            remote_side="StockIndustry.industry_code",
            foreign_keys="[StockIndustry.parent_code]",
        ),
    )
    children: List["StockIndustry"] = Relationship(back_populates="parent")

    stock_mappings: List["StockIndustryMapping"] = Relationship(
        back_populates="industry"
    )

    def __repr__(self):
        return f"<Industry(code='{self.industry_code}', name='{self.name}')>"


class StockIndustryCreate(StockIndustryBase):
    """创建股票行业请求模型"""


class StockIndustryUpdate(SQLModel):
    """更新股票行业请求模型"""

    name: Optional[str] = Field(max_length=50)
    level: Optional[int]
    parent_code: Optional[str] = Field(max_length=20)
    component_count: Optional[int]
    pe_ratio: Optional[float]
    pe_ratio_ttm: Optional[float]
    pb_ratio: Optional[float]
    dividend_yield: Optional[float]


class StockIndustryMappingBase(SQLModel):
    symbol: str = Field(
        foreign_key="stock_basic_info.symbol", max_length=10, nullable=False
    )  # 股票代码
    industry_code: str = Field(
        foreign_key="stock_industry.industry_code", max_length=20, nullable=False
    )  # 行业代码
    is_main: int = Field(default=1)  # 是否为主要行业(1-是, 0-否)


class StockIndustryMapping(StockIndustryMappingBase, table=True):
    """股票行业关联表"""

    __tablename__ = "stock_industry_mapping"

    id: Optional[int] = Field(default=None, primary_key=True)
    last_update: datetime = Field(
        default_factory=datetime.now(timezone.utc)
    )  # 最后更新时间

    # 唯一约束
    __table_args__ = (
        # SQLModel 的唯一约束需要保留 SQLAlchemy 的写法
        # 注意这里导入 UniqueConstraint
        __import__("sqlalchemy").UniqueConstraint(
            "symbol", "industry_code", name="uix_symbol_industry"
        ),
    )

    # 关系定义
    industry: Optional["StockIndustry"] = Relationship(back_populates="stock_mappings")

    def __repr__(self):
        return f"<IndustryMapping(symbol='{self.symbol}', industry_code={self.industry_code})>"


class StockIndustryMappingCreate(StockIndustryMappingBase):
    """创建股票行业关联请求模型"""


class StockIndustryMappingUpdate(SQLModel):
    """更新股票行业关联请求模型"""

    is_main: Optional[int]
