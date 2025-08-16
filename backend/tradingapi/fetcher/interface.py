from typing import Protocol

import pandas as pd


class StockInfoFetcher(Protocol):
    async def get_all_stock_basic_info(self): ...
    async def fetch_stock_data(
        self, stock_code: str, start_date: str, end_date: str
    ) -> pd.DataFrame: ...


class StockIndustryFetcher(Protocol):
    async def fetch_industry_info(
        self,
    ) -> pd.DataFrame: ...
    async def fetch_single_third_cons(self, industry) -> list[dict]: ...
