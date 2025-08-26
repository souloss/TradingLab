import asyncio

import akshare as ak
import pandas as pd
from loguru import logger

from ..base import DataSourceName, StockDataSource
from ..manager import manager
from .exchange import fetch_bj_stocks, fetch_sh_stocks, fetch_sz_stocks

token = "27127e2b9c9a31e0b6f126568f4c2d4e5fd85a9d"


@manager.register_data_source
class XUEQIU(StockDataSource):
    """雪球数据源"""

    name = DataSourceName.XUEQIU

    def __init__(self):
        super().__init__()

    async def health_check(self) -> bool:
        """检查数据源是否可用"""
        try:
            df = await asyncio.wait_for(
                asyncio.to_thread(ak.stock_individual_spot_xq, token=token),
                timeout=self.timeout,
            )
            return True
        except Exception as ex:
            logger.error(f"健康检查失败, exception:{ex}")
            return False

    async def _fetch_stock_detail(self, exchange: str, symbol: str):
        def _fetch():
            stock_info = ak.stock_individual_spot_xq(
                symbol=exchange.upper() + symbol, token=token
            )
            info_dict = dict(zip(stock_info["item"], stock_info["value"]))
            return {
                "证券代码": symbol,
                "交易所": exchange,
                "名称": info_dict.get("名称", ""),
                "总股本": info_dict.get("基金份额/总股本"),
                "流通股": info_dict.get("流通股"),
                "总市值": info_dict.get("资产净值/总市值"),
                "流通市值": info_dict.get("流通值"),
                "行业": info_dict.get("行业", "UNkNOW"),
                "上市时间": info_dict.get("发行日期", ""),
            }

        try:
            logger.debug(f"开始获取股票详情... {symbol}")
            result = await asyncio.to_thread(_fetch)
            logger.debug(f"股票详情获取成功... {result}")
            return result
        except Exception as e:
            logger.error(f"获取股票详情失败: {e}")
            return {}

    def _clean_numeric_columns(self, stocks: pd.DataFrame):
        numeric_cols = ["总股本", "流通股", "总市值", "流通市值"]
        for col in numeric_cols:
            stocks[col] = pd.to_numeric(stocks[col], errors="coerce")
        return stocks

    def _format_listing_date(self, stocks: pd.DataFrame):
        stocks["上市时间"] = pd.to_datetime(
            stocks["上市时间"], format="%Y%m%d", errors="coerce"
        )
        # 将 NaT 转为 None，Timestamp 转为 date
        stocks["上市时间"] = stocks["上市时间"].apply(
            lambda x: x.date() if pd.notna(x) else None
        )
        return stocks

    def _log_and_drop_invalid_rows(
        self, df: pd.DataFrame, required_cols: list
    ) -> pd.DataFrame:
        """
        打印必填字段缺失的行，并删除
        """
        mask_invalid = df[required_cols].isna().any(axis=1)
        if mask_invalid.any():
            logger.warning(
                f"存在不符合必填字段规范的行，将被删除:\n{df.loc[mask_invalid]}"
            )
        return df.loc[~mask_invalid].copy()

    @manager.register_method(weight=1.2, max_requests_per_minute=30, max_concurrent=5)
    async def get_stock_basic_info(self, exchange, symbol):
        return await self._fetch_stock_detail(exchange=exchange, symbol=symbol)

    @manager.register_method(weight=1.2, max_requests_per_minute=30, max_concurrent=5)
    async def get_all_stock_basic_info(self):
        sz, sh, bj = await asyncio.gather(
            fetch_sz_stocks(), fetch_sh_stocks(), fetch_bj_stocks()
        )
        stocks = pd.concat([sz, sh, bj], ignore_index=True)

        new_cols = [
            "名称",
            "总股本",
            "流通股",
            "总市值",
            "流通市值",
            "行业",
            "上市时间",
        ]

        # 初始化新列
        for col in new_cols:
            stocks[col] = None

        # 并发获取股票详情
        tasks = [
            self._fetch_stock_detail(stock["交易所"], stock["证券代码"])
            for stock in stocks
        ]
        results = await asyncio.gather(*tasks)

        # 将结果填充回 DataFrame
        for detail in results:
            code = detail.get("证券代码")  # _fetch_stock_detail 返回时加上 code
            if not code:
                continue
            for col in new_cols:
                stocks.loc[stocks["证券代码"] == code, col] = detail.get(col)

        # 清洗
        stocks = self._clean_numeric_columns(stocks)
        stocks = self._format_listing_date(stocks)
        stocks = self._log_and_drop_invalid_rows(
            stocks, required_cols=["名称", "交易所", "板块"]
        )

        # 排序列
        final_columns = [
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
        return stocks[final_columns]
