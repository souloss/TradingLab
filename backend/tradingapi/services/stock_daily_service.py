import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

import pandas as pd
from chinese_calendar import is_holiday
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from tradingapi.fetcher.interface import StockInfoFetcher
from tradingapi.fetcher.manager import manager
from tradingapi.models import StockDailyData
from tradingapi.repositories.stock_basic_info import StockBasicInfoRepository
from tradingapi.repositories.stock_daily_data import (StockDailyRepository,
                                                      daily_data_to_dataframe)


class StockDailyService:
    def __init__(self, session: AsyncSession):
        self.repo = StockDailyRepository(session)
        self.basic_repo = StockBasicInfoRepository(session)

    # 根据股票代码，日期范围获取日线数据
    async def get_daily_by_code(
        self, code: str, start_date: date, end_date: date
    ) -> pd.DataFrame:
        # 1. 日期标准化
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        # 2. 尝试从缓存加载数据
        listing_date = await self.basic_repo.get_listing_date_by_symbol(code)
        listing_dt = pd.Timestamp(listing_date) if listing_date else None

        # 如果请求开始日期早于上市日期，则调整为上市日期
        adjusted_start_dt = max(start_dt, listing_dt) if listing_dt else start_dt

        # 如果调整后开始日期晚于结束日期，则没有数据
        if adjusted_start_dt > end_dt:
            logger.warning(
                f"请求日期范围 {start_dt} 至 {end_dt} 早于上市日期 {listing_date}"
            )
            return pd.DataFrame()
        
        daily_data = await self.repo.get_daily_data(code, adjusted_start_dt, end_dt)
        cached_df = daily_data_to_dataframe(daily_data)
        missing_days = []

        # 3. 检查缓存是否满足当前请求
        if not cached_df.empty:
            # 3.1 获取缓存日期范围
            cache_min = cached_df.index.min()
            cache_max = cached_df.index.max()

            req_dates = pd.date_range(start=cache_min, end=cache_max, freq="B")
            # 进一步排除节假日（传入节假日列表）
            trading_days = [d for d in req_dates if is_trading_day(d.to_pydatetime())]
            # 3.2 检查缓存是否覆盖所有交易日
            cached_dates = cached_df.index
            missing_days = [d for d in trading_days if d not in cached_dates]
            # 如果没有任何交易日缺失，则使用缓存
            if not missing_days:
                logger.debug(f"缓存满足要求: {code} ({adjusted_start_dt} 至 {end_date})")
                return _filter_date_range(cached_df, adjusted_start_dt, end_dt).copy()

        # 4. 确定需要获取的数据范围
        fetch_ranges = _merge_consecutive_dates(missing_days) if missing_days else [(start_date, end_date)]

        # 5. 获取缺失数据
        new_dfs = []
        stock_fetcher: StockInfoFetcher = manager.bind(StockInfoFetcher)
        logger.debug(f"需要获取缺失数据: {fetch_ranges}, missday:{missing_days}")

        tasks = [
            stock_fetcher.fetch_stock_data(
                code, fetch_start.isoformat(), fetch_end.isoformat()
            )
            for fetch_start, fetch_end in fetch_ranges
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        new_dfs = []
        for (fetch_start, fetch_end), result in zip(fetch_ranges, results):
            if isinstance(result, Exception):
                logger.error(f"获取失败[{fetch_start} - {fetch_end}]: {result}")
            elif result is None or result.empty:
                logger.warning(f"空数据: {code} ({fetch_start}至{fetch_end})")
            else:
                logger.info(f"成功获取: {code} ({fetch_start}至{fetch_end})")
                new_dfs.append(result)

        # 6. 合并缓存和新数据
        combined_df = _merge_data(cached_df, new_dfs)

        # 7. 新数据不为空，才有必要重新保存
        if new_dfs:
            await self.repo.upsert_stock_dailys_bydf(combined_df)

        # 8. 返回请求日期范围内的数据
        return (
            _filter_date_range(combined_df, start_dt, end_dt).copy()
            if not combined_df.empty
            else pd.DataFrame()
        )


# 新增：判断是否为交易日的函数（考虑周末和节假日）
def is_trading_day(date):
    # 1. 排除周末 (周一=0, 周日=6)
    if date.weekday() >= 5:
        return False
    # 2. 排除节假日
    date_date = date.date()  # 转换为date类型进行比较
    if is_holiday(date_date):
        return False
    return True


def _merge_consecutive_dates(dates_list):
    """
    将连续的日期合并为范围元组 [(start_date, end_date)]

    参数:
        dates_list: 排好序的日期列表 (pandas.Timestamp 列表)

    返回:
        元组列表: [(start_date, end_date), ...]
    """
    if not dates_list:
        return []

    # 确保日期排序
    sorted_dates = sorted(dates_list)

    ranges = []
    start = end = sorted_dates[0]

    for date in sorted_dates[1:]:
        # 检查是否是连续日期（相差1天）
        if (date - end).days == 1:
            end = date
        else:
            # 将当前范围添加到结果
            ranges.append((start, end))
            # 开始新范围
            start = end = date

    # 添加最后一个范围
    ranges.append((start, end))

    return ranges


def _merge_data(cached_df: pd.DataFrame, new_dfs: list) -> pd.DataFrame:
    """
    合并缓存数据和新获取的数据

    参数:
        cached_df: 缓存数据
        new_dfs: 新获取的数据列表

    返回:
        合并后的DataFrame
    """
    # 1. 没有新数据 - 直接返回缓存
    if not new_dfs:
        return cached_df.copy()

    # 2. 没有缓存数据 - 合并所有新数据
    if cached_df.empty:
        combined_df = pd.concat(new_dfs)

    # 3. 有缓存数据 - 合并缓存和新数据
    else:
        combined_df = pd.concat([cached_df] + new_dfs)

    # 4. 数据清洗
    combined_df = combined_df.sort_index()  # 按日期排序
    combined_df = combined_df[~combined_df.index.duplicated(keep="first")]  # 去重

    return combined_df


def _filter_date_range(
    df: pd.DataFrame, start_dt: pd.Timestamp, end_dt: pd.Timestamp
) -> pd.DataFrame:
    """
    筛选指定日期范围内的数据
    参数:
        df: 原始数据，可以包含日期列或DatetimeIndex
        start_dt: 开始日期（pd.Timestamp）
        end_dt: 结束日期（pd.Timestamp）
    返回:
        筛选后的DataFrame
    """
    # 检查是否已有DatetimeIndex
    if isinstance(df.index, pd.DatetimeIndex):
        # 直接使用索引进行范围筛选
        mask = (df.index >= start_dt) & (df.index <= end_dt)
        return df.loc[mask]
    else:
        # 检查是否有日期列
        date_columns = [col for col in df.columns if 'date' in col.lower()]
        if not date_columns:
            raise ValueError(f"DataFrame既没有DatetimeIndex，也没有日期列。可用列: {df.columns.tolist()}")
        
        # 使用找到的日期列
        date_col = date_columns[0]
        # 确保日期列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
            df[date_col] = pd.to_datetime(df[date_col])
        
        # 筛选日期范围
        mask = (df[date_col] >= start_dt) & (df[date_col] <= end_dt)
        return df.loc[mask]