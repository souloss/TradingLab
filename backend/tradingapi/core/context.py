import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any, Dict, Optional

from fastapi import Request
from loguru import logger

# 上下文变量
request_context: ContextVar[Dict[str, Any]] = ContextVar("request_context", default={})


class RequestContext:
    """请求上下文管理器"""

    def __init__(self, trace_id: str, user_id: Optional[str] = None):
        self.trace_id = trace_id
        self.user_id = user_id
        self.extra_data = {}

    def set_data(self, key: str, value: Any):
        """设置上下文数据"""
        self.extra_data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return self.extra_data.get(key, default)

    @classmethod
    def current(cls) -> Optional["RequestContext"]:
        """获取当前请求上下文"""
        ctx_data = request_context.get({})
        if not ctx_data:
            return None

        context = cls(ctx_data.get("trace_id", ""), ctx_data.get("user_id"))
        context.extra_data = ctx_data.get("extra_data", {})
        return context

    def __enter__(self):
        """进入上下文"""
        ctx_data = {
            "trace_id": self.trace_id,
            "user_id": self.user_id,
            "extra_data": self.extra_data,
        }
        request_context.set(ctx_data)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        request_context.set({})


# 中间件
async def request_context_middleware(request: Request, call_next):
    """请求上下文中间件"""
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")

    # 设置到 request state 中，供异常处理器使用
    request.state.trace_id = trace_id

    with RequestContext(trace_id, user_id) as ctx:
        # 记录请求开始
        logger.bind(trace_id=trace_id, user_id=user_id).info(
            f"Request started: {request.method} {request.url}"
        )

        response = await call_next(request)

        # 添加追踪ID到响应头
        response.headers["X-Trace-ID"] = trace_id

        # 记录请求结束
        logger.bind(trace_id=trace_id, user_id=user_id).info(
            f"Request completed: {response.status_code}"
        )

        return response
