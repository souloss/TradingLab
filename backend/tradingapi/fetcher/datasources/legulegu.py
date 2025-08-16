import asyncio

import akshare as ak
import pandas as pd
from loguru import logger

from ..base import DataSourceName, StockDataSource
from ..manager import manager


@manager.register_data_source
class Legulegu(StockDataSource):
    """乐咕乐股数据源"""

    name = DataSourceName.Legulegu

    def __init__(self):
        super().__init__()

    async def health_check(self) -> bool:
        """检查数据源是否可用"""
        return True

    async def fetch_sw_first_info(
        self,
    ) -> pd.DataFrame:
        """获取申万一级行业"""
        df = await asyncio.to_thread(ak.sw_index_first_info)
        df["上级行业"] = ""
        df["行业级别"] = 1
        logger.debug(f"一级行业获取成功, 数量:{len(df)}")
        return df

    async def fetch_sw_second_info(self, first_df: pd.DataFrame) -> pd.DataFrame:
        """获取申万二级行业"""
        df = await asyncio.to_thread(ak.sw_index_second_info)
        df["行业级别"] = 2
        name_to_code = dict(zip(first_df["行业名称"], first_df["行业代码"]))
        df["上级行业"] = df["上级行业"].map(name_to_code)
        logger.debug(f"二级行业获取成功, 数量:{len(df)}")
        return df

    async def fetch_sw_third_info(self, second_df: pd.DataFrame) -> pd.DataFrame:
        """获取申万三级行业"""
        df = await asyncio.to_thread(ak.sw_index_third_info)
        df["行业级别"] = 3
        name_to_code_2 = dict(zip(second_df["行业名称"], second_df["行业代码"]))
        df["上级行业"] = df["上级行业"].map(name_to_code_2)
        logger.debug(f"三级行业获取成功, 数量:{len(df)}")
        return df

    @manager.register_method(weight=1.0, max_requests_per_minute=30, max_concurrent=3)
    async def fetch_industry_info(
        self,
    ) -> pd.DataFrame:
        """获取全量申万行业（并发）"""
        first_df = await self.fetch_sw_first_info()
        second_df = await self.fetch_sw_second_info(first_df)
        third_df = await self.fetch_sw_third_info(second_df)

        result = pd.concat([first_df, second_df, third_df], ignore_index=True)
        return result

    @manager.register_method(weight=1.0, max_requests_per_minute=30, max_concurrent=3)
    async def fetch_single_third_cons(self, industry) -> list[dict]:
        """获取单个三级行业成分股"""
        industry_code = industry.industry_code
        industry_name = industry.name
        try:
            logger.debug(
                f"获取行业代码:{industry_code}，行业名称:{industry_name}的成分股"
            )
            cons_df = await asyncio.to_thread(
                ak.sw_index_third_cons, symbol=industry_code
            )

            mappers = []
            for _, stock_row in cons_df.iterrows():
                stock_code = stock_row["股票代码"].split(".")[0]
                mappers.append(
                    {"symbol": stock_code, "industry_code": industry_code, "is_main": 1}
                )
                logger.debug(f"获取映射: {stock_code}:{industry_code}({industry_name})")
            logger.debug(f"获取完成, 数量为{len(cons_df)}")
            return mappers
        except Exception as e:
            logger.warning(f"获取失败，异常: {str(e)}")
            return []

    async def fetch_third_industry_cons(self, third_industries) -> list[dict]:
        tasks = [self.fetch_single_third_cons(ind) for ind in third_industries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        merged = []
        for r in results:
            if isinstance(r, Exception):
                logger.warning(f"fetch_single_third_cons 子任务异常: {r}")
                continue
            merged.extend(r)
        return merged
