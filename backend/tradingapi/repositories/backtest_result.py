from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, SQLModel

from tradingapi.models.backtest_result import BacktestResult
from tradingapi.repositories.base import BaseRepository


class BacktestResultRepository(BaseRepository[BacktestResult]):
    """回测结果仓库类"""

    model_type = BacktestResult

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model_type=self.model_type)
