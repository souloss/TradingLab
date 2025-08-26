# models/stock_basic_info.py
from datetime import date
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from tradingapi.models.stock_basic_info import StockBasicInfo
from tradingapi.repositories.base import BaseRepository


class StockBasicInfoRepository(BaseRepository[StockBasicInfo]):
    """股票基本信息仓库类"""

    model_type = StockBasicInfo

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_type=self.model_type)

    async def get_stock_by_symbol(self, symbol: str) -> Optional[StockBasicInfo]:
        """根据股票代码获取股票基本信息"""
        stmt = select(self.model_type).where(self.model_type.symbol == symbol)
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def get_listing_date_by_symbol(self, symbol: str) -> Optional[date]:
        """根据股票代码获取上市日期"""
        stmt = select(self.model_type.listing_date).where(
            self.model_type.symbol == symbol
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def get_stock_name_by_symbol(self, symbol: str) -> Optional[str]:
        """根据股票代码获取股票名称"""
        stmt = select(self.model_type.name).where(self.model_type.symbol == symbol)
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def get_filter_options(self) -> Dict[str, List[str]]:
        """返回前端 StockFilterOptions 所需的所有下拉选项"""

        async def _distinct(col):
            stmt = select(col).where(col.isnot(None)).distinct()
            return (await self.session.execute(stmt)).scalars().all()

        return {
            "exchanges": await _distinct(self.model_type.exchange),
            "industries": await _distinct(self.model_type.industry),
            "stockTypes": await _distinct(self.model_type.stock_type),
            "sections": await _distinct(self.model_type.section),
        }

    async def advanced_filter(
        self,
        exchanges: Optional[List[str]] = None,
        sections: Optional[List[str]] = None,
        stock_types: Optional[List[str]] = None,
        industries: Optional[List[str]] = None,
        start_listing_date: Optional[date] = None,
        end_listing_date: Optional[date] = None,
        min_total_market_value: Optional[float] = None,
        max_total_market_value: Optional[float] = None,
        min_float_market_value: Optional[float] = None,
        max_float_market_value: Optional[float] = None,
        min_total_shares: Optional[float] = None,
        max_total_shares: Optional[float] = None,
        min_float_shares: Optional[float] = None,
        max_float_shares: Optional[float] = None,
        keyword: Optional[str] = None,
    ) -> List[StockBasicInfo]:
        """高级组合过滤方法"""
        # 构建查询语句
        query = select(StockBasicInfo)

        # 交易所过滤
        if exchanges:
            query = query.filter(self.model_type.exchange.in_(exchanges))

        # 板块过滤
        if sections:
            query = query.filter(self.model_type.section.in_(sections))

        # 股票类型过滤
        if stock_types:
            query = query.filter(self.model_type.stock_type.in_(stock_types))

        # 行业过滤
        if industries:
            query = query.filter(self.model_type.industry.in_(industries))

        # 上市日期范围过滤
        if start_listing_date or end_listing_date:
            if start_listing_date and end_listing_date:
                query = query.filter(
                    self.model_type.listing_date.between(
                        start_listing_date, end_listing_date
                    )
                )
            elif start_listing_date:
                query = query.filter(self.model_type.listing_date >= start_listing_date)
            else:
                query = query.filter(self.model_type.listing_date <= end_listing_date)

        # 总市值过滤
        if min_total_market_value or max_total_market_value:
            if min_total_market_value and max_total_market_value:
                query = query.filter(
                    self.model_type.total_market_value.between(
                        min_total_market_value, max_total_market_value
                    )
                )
            elif min_total_market_value:
                query = query.filter(
                    self.model_type.total_market_value >= min_total_market_value
                )
            else:
                query = query.filter(
                    self.model_type.total_market_value <= max_total_market_value
                )

        # 流通市值过滤
        if min_float_market_value or max_float_market_value:
            if min_float_market_value and max_float_market_value:
                query = query.filter(
                    self.model_type.float_market_value.between(
                        min_float_market_value, max_float_market_value
                    )
                )
            elif min_float_market_value:
                query = query.filter(
                    self.model_type.float_market_value >= min_float_market_value
                )
            else:
                query = query.filter(
                    self.model_type.float_market_value <= max_float_market_value
                )

        # 总股本过滤
        if min_total_shares or max_total_shares:
            if min_total_shares and max_total_shares:
                query = query.filter(
                    self.model_type.total_shares.between(
                        min_total_shares, max_total_shares
                    )
                )
            elif min_total_shares:
                query = query.filter(self.model_type.total_shares >= min_total_shares)
            else:
                query = query.filter(self.model_type.total_shares <= max_total_shares)

        # 流通股本过滤
        if min_float_shares or max_float_shares:
            if min_float_shares and max_float_shares:
                query = query.filter(
                    self.model_type.float_shares.between(
                        min_float_shares, max_float_shares
                    )
                )
            elif min_float_shares:
                query = query.filter(self.model_type.float_shares >= min_float_shares)
            else:
                query = query.filter(self.model_type.float_shares <= max_float_shares)

        # 关键词过滤
        if keyword:
            query = query.filter(
                or_(
                    self.model_type.symbol.contains(keyword),
                    self.model_type.name.contains(keyword),
                )
            )

        result = await self.session.execute(query)
        return result.scalars().all()


def dataframe_to_stock_data(df: pd.DataFrame) -> List[StockBasicInfo]:
    """
    将指定格式的 DataFrame 转换为 StockBasicInfo 对象列表

    :param df: 包含股票基础数据的 DataFrame
    :return: StockBasicInfo 对象列表
    """
    # 确保 DataFrame 包含所有必要的列
    required_columns = [
        "交易所",
        "板块",
        "股票类型",
        "证券代码",
        "名称",
        "上市时间",
        "行业",
        "总股本",
        "流通股",
        "总市值",
        "流通市值",
    ]

    if not all(col in df.columns for col in required_columns):
        missing = [col for col in required_columns if col not in df.columns]
        raise ValueError(f"DataFrame {df.columns}, {df.index} 缺少必要的列: {missing}")

    # # 确保索引是日期类型
    # if not isinstance(df.index, pd.DatetimeIndex):
    #     raise TypeError("DataFrame 索引必须是 DatetimeIndex 类型")

    # 创建存储结果的列表
    stock_data_list = []
    # 遍历 DataFrame 的每一行
    for idx, row in df.iterrows():
        # 将索引转换为日期对象
        # 创建 StockDailyData 对象并添加到列表
        daily_data = StockBasicInfo(
            symbol=row["证券代码"],
            exchange=row["交易所"],
            section=row["板块"],
            stock_type=row["股票类型"],
            name=row["名称"],
            listing_date=row["上市时间"],
            industry=row["行业"],
            total_shares=row["总股本"],
            float_shares=row["流通股"],
            total_market_value=row["总市值"],
            float_market_value=row["流通市值"],
        )
        stock_data_list.append(daily_data)

    return stock_data_list
