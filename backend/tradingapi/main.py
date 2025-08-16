# app/main.py (完整版本)
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from tradingapi.api.v1 import backtest_controller, stock_controller
from tradingapi.core.config import app_config
from tradingapi.core.context import request_context_middleware
from tradingapi.core.db import db_manager
from tradingapi.core.exceptions import (BusinessException,
                                        business_exception_handler,
                                        general_exception_handler,
                                        http_exception_handler,
                                        validation_exception_handler)
from tradingapi.core.initializer import lifespan
from tradingapi.core.metrics import metrics_collector, metrics_middleware
from tradingapi.fetcher.manager import manager


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="Trading API",
        description="Advanced stock backtesting and strategy API",
        version="0.0.1",
        lifespan=lifespan,
        openapi_url=f"/v1/openapi.json" if app_config.DEBUG else None,
        docs_url="/docs" if app_config.DEBUG else None,
        redoc_url="/redoc" if app_config.DEBUG else None,
    )
    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_config.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 添加中间件
    app.middleware("http")(request_context_middleware)
    app.middleware("http")(metrics_middleware)

    # 注册异常处理器
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # 注册路由
    app.include_router(backtest_controller.router, prefix="/api/v1")
    app.include_router(stock_controller.router, prefix="/api/v1")

    # 健康检查和指标端点
    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "fetcher_stat": await manager.stat(),
        }

    @app.get("/metrics")
    async def get_metrics():
        """获取应用指标"""
        return metrics_collector.get_metrics()

    # 最后挂载静态资源
    static_dir = Path(__file__).with_suffix("").parent / "static" / "public"
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "tradingapi.main:app",
        host="0.0.0.0",
        port=8000,
        reload=app_config.DEBUG,
        log_level="debug" if app_config.DEBUG else "info",
    )
