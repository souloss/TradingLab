from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, SQLModel

from tradingapi.models.backtest_stats import BacktestStatsTable
from tradingapi.repositories.base import BaseRepository


class BacktestStatsRepository(BaseRepository[BacktestStatsTable]):
    """回测统计仓库类"""

    model_type = BacktestStatsTable

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_type=self.model_type)
