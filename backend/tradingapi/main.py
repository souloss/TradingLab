import sys
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


def get_static_dir() -> Path:
    """获取静态文件目录路径"""
    # 检查是否是打包后的环境
    if getattr(sys, "frozen", False):
        # 打包后的路径
        base_path = Path(sys._MEIPASS)
    else:
        # 开发环境路径
        base_path = Path(__file__).parent

    # 静态文件目录
    static_dir = base_path / "static" / "public"

    # 如果目录不存在，尝试其他可能的路径
    if not static_dir.exists():
        # 尝试相对于可执行文件的路径
        exe_dir = Path(sys.executable).parent
        alternative_path = exe_dir / "static" / "public"
        if alternative_path.exists():
            static_dir = alternative_path

    return static_dir


def is_packaged() -> bool:
    """检查是否是打包后的应用"""
    return getattr(sys, "frozen", False)


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

    # 修改静态文件路径处理
    static_dir = get_static_dir()
    # 检查静态文件目录是否存在
    if static_dir.exists():
        # 挂载静态资源
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
        logger.info(f"Static files mounted from: {static_dir}")
    else:
        logger.warning(f"Static files directory not found: {static_dir}")
    
    @app.exception_handler(404)
    async def not_found(request: Request, exc):
        return FileResponse(static_dir / "index.html")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    # 检查是否是打包后的应用
    if is_packaged():
        # 打包后的应用 - 禁用重载器
        uvicorn.run(
            app=app,
            host="0.0.0.0",
            port=8000,
            reload=False,  # 禁用重载器
            log_level="info",
        )
    else:
        # 开发环境 - 根据配置决定是否启用重载器
        uvicorn.run(
            "tradingapi.main:app",
            host="0.0.0.0",
            port=8000,
            reload=app_config.DEBUG,
            log_level="debug" if app_config.DEBUG else "info",
        )
