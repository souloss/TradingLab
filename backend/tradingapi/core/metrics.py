import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, Optional

from loguru import logger


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self.request_count = defaultdict(int)
        self.request_duration = defaultdict(deque)
        self.error_count = defaultdict(int)
        self.active_connections = 0

    def record_request(
        self, endpoint: str, method: str, duration: float, status_code: int
    ):
        """记录请求指标"""
        key = f"{method}:{endpoint}"
        self.request_count[key] += 1

        # 保留最近1000次请求的响应时间
        duration_queue = self.request_duration[key]
        duration_queue.append(duration)
        if len(duration_queue) > 1000:
            duration_queue.popleft()

        # 记录错误
        if status_code >= 400:
            self.error_count[key] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        metrics = {
            "request_count": dict(self.request_count),
            "error_count": dict(self.error_count),
            "active_connections": self.active_connections,
            "response_time_stats": {},
        }

        # 计算响应时间统计
        for key, durations in self.request_duration.items():
            if durations:
                sorted_durations = sorted(durations)
                count = len(sorted_durations)
                metrics["response_time_stats"][key] = {
                    "avg": sum(sorted_durations) / count,
                    "min": sorted_durations[0],
                    "max": sorted_durations[-1],
                    "p50": sorted_durations[count // 2],
                    "p95": sorted_durations[int(count * 0.95)],
                    "p99": sorted_durations[int(count * 0.99)],
                }

        return metrics


# 全局指标收集器
metrics_collector = MetricsCollector()


def monitor_performance(operation_name: Optional[str] = None):
    """性能监控装饰器"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            operation = operation_name or f"{func.__module__}.{func.__name__}"

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                logger.debug(f"Operation {operation} completed in {duration:.3f}s")
                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.warning(f"Operation {operation} failed in {duration:.3f}s: {e}")
                raise

        return wrapper

    return decorator


# 中间件
async def metrics_middleware(request, call_next):
    """指标收集中间件"""
    start_time = time.time()
    metrics_collector.active_connections += 1

    try:
        response = await call_next(request)
        duration = time.time() - start_time

        # 记录请求指标
        metrics_collector.record_request(
            endpoint=request.url.path,
            method=request.method,
            duration=duration,
            status_code=response.status_code,
        )

        return response

    finally:
        metrics_collector.active_connections -= 1
