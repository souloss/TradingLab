# app/api/backtest_controller.py
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from tradingapi.core.db import get_session
from tradingapi.schemas.backtest import *
from tradingapi.schemas.response import APIResponse, PaginatedResponse
from tradingapi.services.backtest_stats_service import BacktestService

router = APIRouter(prefix="/backtest", tags=["backtest"])


# 列出所有回测结果
@router.get(
    "", response_model=APIResponse[PaginatedResponse[BacktestListItem]]
)
async def list_backtests(
    page: int = Query(1, ge=1, description="当前页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页大小"),
    keyword: Optional[str] = Query(
        None, description="搜索关键字（股票代码/名称/策略名）"
    ),
    session: AsyncSession = Depends(get_session),
):
    service = BacktestService(session)
    ret = await service.list_paged(page=page, page_size=pageSize, keyword=keyword)
    return APIResponse.success(ret)

# 个股回测
@router.post(
    "/stock",
    response_model=APIResponse[BacktestResponse],
)
async def backtest_by_stock(
    req: BacktestRequest, session: AsyncSession = Depends(get_session)
):
    service = BacktestService(session)
    ret = await service.backtest(req)
    return APIResponse.success(ret)


# 多股回测
@router.post("/stocks", response_model=APIResponse[BacktestResults])
async def backtest_by_stocks(
    reqs: List[BacktestRequest], session: AsyncSession = Depends(get_session)
):
    service = BacktestService(session)
    ret = await service.backtest_batch(reqs)
    logger.debug(f"批量回测成功，返回数据{ret}")
    return APIResponse.success(ret)


# 获取回测结果
@router.get("/{backtest_id}", response_model=APIResponse[BacktestResponse])
async def get_backtest(backtest_id: str, session: AsyncSession = Depends(get_session)):
    service = BacktestService(session)
    results = await service.get_by_id(backtest_id)
    return APIResponse.success(results)
