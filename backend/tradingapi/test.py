from typing import Any, Dict, List, Optional

import requests


class BiyingHSClient:
    BASE_URL = "http://api.biyingapi.com"

    def __init__(self, licence: str, timeout: float = 600.0):
        self.licence = licence
        self.timeout = timeout

    def _get(self, path: str, **kwargs) -> Any:
        url = f"{self.BASE_URL}{path}/{self.licence}"
        resp = requests.get(url, timeout=self.timeout, params=kwargs or None)
        resp.raise_for_status()
        return resp.json()

    def stock_list(self) -> List[Dict[str, str]]:
        """获取基础股票列表（dm, mc, jys）"""
        return self._get("/hslt/list")

    def new_stock_calendar(self) -> List[Dict[str, Any]]:
        """获取新股日历"""
        return self._get("/hslt/new")

    def index_tree(self) -> List[Dict[str, Any]]:
        """指数 / 行业 / 概念树接口"""
        return self._get("/hszg/list")

    def index_members(self, code: str) -> List[Dict[str, Any]]:
        """根据指数/行业/概念 code 获取相关股票"""
        return self._get(f"/hszg/gg/{code}")

    def stock_relations(self, stock_code: str) -> List[Dict[str, Any]]:
        """获取股票相关的指数/行业/概念"""
        return self._get(f"/hszg/zg/{stock_code}")

    def pool_zts(self, date: str) -> List[Dict[str, Any]]:
        """涨停股池"""
        return self._get(f"/hslt/ztgc/{date}")

    def pool_dts(self, date: str) -> List[Dict[str, Any]]:
        """跌停股池"""
        return self._get(f"/hslt/dtgc/{date}")

    def pool_qss(self, date: str) -> List[Dict[str, Any]]:
        """强势股池"""
        return self._get(f"/hslt/qsgc/{date}")

    # 你可以继续为“次新股池”、“炸板股池”等接口添加更多方法

    def company_profile(self, stock_code: str) -> List[Dict[str, Any]]:
        """公司简介"""
        return self._get(f"/hscp/gsjj/{stock_code}")

    def stock_daily_data(self, stock_code: str, licence, st, et):
        return self._get(f"/hsstock/indicators/{stock_code}/{licence}?st={st}&et={et}")

    # 请按需继续封装：所属指数、历届高管、财务数据、实时交易、技术指标等


# 简单使用示例：
if __name__ == "__main__":
    licence = "5F3241B2-B718-46B0-8657-A85DA628DF3C"
    client = BiyingHSClient(licence)
    stocks = client.stock_daily_data(
        "001239.SZ", licence=licence, st="20000815", et="20250815"
    )
    import pprint

    pprint.pprint(stocks)
