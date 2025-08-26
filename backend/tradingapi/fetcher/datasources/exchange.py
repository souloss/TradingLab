import asyncio

import akshare as ak
import pandas as pd
from loguru import logger


async def fetch_sz_stocks():
    def _fetch():
        sz_dfs = []
        for stock_type, (param, code_col) in {
            "A股": ("A股列表", "A股代码"),
            "B股": ("B股列表", "B股代码"),
            "AB股": ("AB股列表", "AB股代码"),
            "CDR股": ("CDR列表", "CDR代码"),
        }.items():
            df = ak.stock_info_sz_name_code(param)
            df = df.assign(交易所="SZ", 股票类型=stock_type)
            df = df.rename(columns={code_col: "证券代码"})
            sz_dfs.append(df)
            logger.debug(f"交易所 SZ，股票类型 {stock_type} 获取完成!")
        return pd.concat(sz_dfs)[["交易所", "股票类型", "证券代码", "板块"]]

    return await asyncio.to_thread(_fetch)


async def fetch_sh_stocks():
    def _fetch():
        sh_dfs = []
        for param, stock_type in {
            "主板A股": "A股",
            "主板B股": "B股",
            "科创板": "A股",
        }.items():
            df = ak.stock_info_sh_name_code(param)
            df = df.assign(交易所="SH", 股票类型=stock_type)
            sh_dfs.append(df)
            logger.debug(f"交易所 SH，股票类型 {param} 获取完成!")
        sh_stocks = pd.concat(sh_dfs)
        sh_stocks["板块"] = sh_stocks["证券代码"].apply(
            lambda x: "科创板" if str(x).startswith("688") else "沪市主板"
        )
        return sh_stocks[["交易所", "股票类型", "证券代码", "板块"]]

    return await asyncio.to_thread(_fetch)


async def fetch_bj_stocks():
    def _fetch():
        def get_bj_board(code):
            code_str = str(code)
            if code_str.startswith("82"):
                return "北交优先股"
            elif code_str.startswith(("83", "87")):
                return "北交普通股"
            elif code_str.startswith("88"):
                return "北交公开发行股"
            elif code_str.startswith("920"):
                return "北交新上市公司股"
            else:
                return "北交所"

        bj_stocks = ak.stock_info_bj_name_code()
        bj_stocks["交易所"] = "BJ"
        bj_stocks["股票类型"] = "A股"
        bj_stocks["板块"] = bj_stocks["证券代码"].apply(get_bj_board)
        logger.debug(f"交易所 BJ 数据获取完成!")
        return bj_stocks[["交易所", "股票类型", "证券代码", "板块"]]

    return await asyncio.to_thread(_fetch)


async def fetch_all_stocks():
    sz, sh, bj = await asyncio.gather(
        fetch_sz_stocks(), fetch_sh_stocks(), fetch_bj_stocks()
    )
    stocks = pd.concat([sz, sh, bj], ignore_index=True)
    return stocks
