import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from tradingapi.models.stock_industry import StockIndustry
from tradingapi.repositories.base import BaseRepository


class StockIndustryRepository(BaseRepository[StockIndustry]):
    model_type = StockIndustry

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_type=self.model_type)


def industry_to_dataframe(industry_list):
    """
    将 StockIndustry 对象列表转换为指定格式的 DataFrame
    :param industry_list: StockIndustry 对象列表
    :return: 格式化后的 DataFrame
    """
    # 创建空列表存储数据
    data = {
        "行业代码": [],
        "行业名称": [],
        "行业级别": [],
        "上级行业代码": [],
        "成份个数": [],
        "静态市盈率": [],
        "TTM市盈率": [],
        "市净率": [],
        "静态股息率": [],
    }

    # 填充数据
    for industry in industry_list:
        data["行业代码"].append(industry.industry_code)
        data["行业名称"].append(industry.name)
        data["行业级别"].append(industry.level)
        data["上级行业代码"].append(industry.parent_code)
        data["成份个数"].append(industry.component_count)
        data["静态市盈率"].append(industry.pe_ratio)
        data["TTM市盈率"].append(industry.pe_ratio_ttm)
        data["市净率"].append(industry.pb_ratio)
        data["静态股息率"].append(industry.dividend_yield)

    # 创建 DataFrame
    df = pd.DataFrame(data)

    return df
