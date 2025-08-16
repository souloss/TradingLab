from typing import Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from tradingapi.core.db import get_session
from tradingapi.schemas.response import APIResponse
from tradingapi.schemas.stocks import (StockBasicInfoFilter,
                                       StockBasicInfoSchema)
from tradingapi.services.stock_service import StocksService

router = APIRouter(prefix="/stocks", tags=["stocks"])


# 示例路由
@router.get(f"", response_model=APIResponse[List[StockBasicInfoSchema]])
async def list_stocks(session: AsyncSession = Depends(get_session)):
    service = StocksService(session)
    results = await service.list_all()
    return APIResponse.success(results)


@router.post(f"/filter", response_model=APIResponse[List[StockBasicInfoSchema]])
async def filter_stocks(
    filter: StockBasicInfoFilter,
    session: AsyncSession = Depends(get_session),
):
    service = StocksService(session)
    results = await service.filter_stock(filter)
    return APIResponse.success(results)


@router.get(f"/filter-options", response_model=APIResponse[Dict[str, List[str]]])
async def filter_stocks(
    session: AsyncSession = Depends(get_session),
):
    service = StocksService(session)
    results = await service.get_filter_options()
    return APIResponse.success(results)
