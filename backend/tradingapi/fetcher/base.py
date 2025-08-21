from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Optional


class DataSourceName(Enum):
    """数据源名称枚举"""

    EASTMONEY = "东方财富"
    Legulegu  = "乐咕乐股"
    TX        = "腾讯"
    Sina      = "新浪"
    XUEQIU    = "雪球"


class StockDataSource(ABC):
    """股票数据源抽象基类"""

    def __init__(self):
        self.is_healthy: bool = True  # 数据源健康状态
        self.last_check_time: Optional[datetime] = None
        self.proxy: Optional[str] = None  # 代理设置
        self.timeout: int = 10  # 请求超时时间(秒)

    @abstractmethod
    async def health_check(self) -> bool:
        """检查数据源是否可用"""
        pass

    def set_proxy(self, proxy: str):
        """设置代理"""
        self.proxy = proxy

    def set_timeout(self, timeout: int):
        """设置超时时间"""
        self.timeout = timeout


import asyncio
from functools import wraps
from typing import Any, Callable, Coroutine, Optional, Union

from aiolimiter import AsyncLimiter


def rate_limited(
    limiter: Optional[AsyncLimiter] = None,
    semaphore: Optional[asyncio.Semaphore] = None,
):
    """
    通用限流装饰器: 支持 QPS + 并发量双重限制
    用法:
        @rate_limited(limiter=AsyncLimiter(10, 1), semaphore=asyncio.Semaphore(5))
        async def fetch_xxx(...):
            ...
    """

    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async def _execute():
                return await func(*args, **kwargs)

            if limiter and semaphore:
                async with limiter:
                    async with semaphore:
                        return await _execute()
            elif limiter:
                async with limiter:
                    return await _execute()
            elif semaphore:
                async with semaphore:
                    return await _execute()
            else:
                return await _execute()

        return wrapper

    return decorator
