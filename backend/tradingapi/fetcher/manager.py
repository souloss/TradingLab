import asyncio
import inspect
import random
from datetime import datetime, timedelta
from functools import partial, wraps
from types import SimpleNamespace
from typing import (Any, Callable, Coroutine, Dict, Generic, List, Optional,
                    Set, Tuple, Type, TypeVar, Union)

from aiolimiter import AsyncLimiter
from loguru import logger
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential_jitter

from .base import DataSourceName, StockDataSource

T = TypeVar("T", bound=StockDataSource)
MethodType = TypeVar("MethodType", bound=Callable)


class MethodRegistry:
    """方法注册信息容器"""

    def __init__(self, method: Callable, weight: float = 1.0):
        self.method = method
        self.weight = weight
        self.limiter: Optional[AsyncLimiter] = None
        self.semaphore: Optional[asyncio.Semaphore] = None
        self.active_tasks: Set[int] = set()
        self.call_count = 0
        self.error_count = 0
        self.last_call_time: Optional[datetime] = None
        self.success_rate: float = 1.0  # 初始成功率100%
        self._ema_alpha = 0.2  # 可配置
        self.data_source: Optional[StockDataSource] = None  # 关联的数据源

    def update_limits(
        self,
        max_requests_per_minute: Optional[int] = None,
        max_concurrent: Optional[int] = None,
    ):
        self.qps_cfg = max_requests_per_minute
        self.concurrent_cfg = max_concurrent
        self.limiter = (
            AsyncLimiter(max_requests_per_minute, 60)
            if max_requests_per_minute
            else None
        )
        self.semaphore = asyncio.Semaphore(max_concurrent) if max_concurrent else None

    def update_weight(self, weight: float):
        """更新权重"""
        self.weight = weight

    def record_success(self):
        """记录成功调用"""
        self.call_count += 1
        self.last_call_time = datetime.now()
        # 滑动窗口/指数衰减成功率
        self.success_rate = (
            1 - self._ema_alpha
        ) * self.success_rate + self._ema_alpha * 1.0

    def record_error(self):
        """记录错误调用"""
        self.call_count += 1
        self.error_count += 1
        self.last_call_time = datetime.now()
        # 滑动窗口/指数衰减失败率
        self.success_rate = (
            1 - self._ema_alpha
        ) * self.success_rate + self._ema_alpha * 0.0

    def get_stats(self) -> dict:
        """获取方法统计信息"""
        return {
            "active_tasks": len(self.active_tasks),
            "call_count": self.call_count,
            "error_count": self.error_count,
            "success_rate": self.success_rate,
            "last_call_time": self.last_call_time,
            "weight": self.weight,
            "qps_limit": self.qps_cfg,
            "concurrent_limit": self.concurrent_cfg,
            "data_source": self.data_source.name.value if self.data_source else None,
        }


class ServiceMethod:
    """服务方法封装器，提供智能调用接口"""

    def __init__(self, name: str, manager: "DataSourceManager"):
        self.name = name
        self.manager = manager
        self.implementations: List[Tuple[StockDataSource, MethodRegistry]] = []

    def add_implementation(self, source: StockDataSource, registry: MethodRegistry):
        """添加方法实现"""
        registry.data_source = source
        self.implementations.append((source, registry))
        logger.info(f"注册方法实现: {self.name} -> {source.name.value}")

    def choose_implementation(self) -> Optional[Tuple[StockDataSource, MethodRegistry]]:
        """根据策略选择最佳实现"""
        available = [(src, reg) for src, reg in self.implementations if src.is_healthy]
        logger.debug(f"选择最佳数据源...，目前可用数据源：{available}")
        if not available:
            return None

        # 计算每个实现的得分
        scores = []
        for src, reg in available:
            load_penalty = 1.0 / (1.0 + len(reg.active_tasks))
            score = reg.weight * reg.success_rate * load_penalty
            scores.append((src, reg, score))

        logger.debug(f"计算出数据源得分:{scores}")
        total = sum(score for _, _, score in scores)
        if total <= 0:
            return random.choice(available)  # fallback：全部分数为0时随机挑一个

        # 加权随机选择
        r = random.uniform(0, total)
        upto = 0
        for src, reg, score in scores:
            upto += score
            if upto >= r:
                return src, reg

        return available[-1]  # 理论上不会走到这里

    async def call(
        self,
        *args,
        limiter: Optional[AsyncLimiter] = None,
        semaphore: Optional[asyncio.Semaphore] = None,
        timeout: Optional[float] = None,
        retries: int = 10,
        **kwargs,
    ) -> Any:
        impl = self.choose_implementation()
        if not impl:
            raise DataSourceUnavailableError(f"没有可用的数据源实现方法: {self.name}")

        source, registry = impl
        method = getattr(source, self.name)  # 已是 wrapper，但 wrapper 只透传

        # 以 per-call 覆盖优先，其次 registry 的默认
        _limiter = limiter or registry.limiter
        _semaphore = semaphore or registry.semaphore

        # 健康检查（必要时）
        if not await self.manager.is_healthy(source.name):
            registry.record_error()
            raise DataSourceUnavailableError(source.name)

        async def _invoke():
            async def _exec():
                return await method(*args, **kwargs)

            if _limiter and _semaphore:
                async with _limiter:
                    async with _semaphore:
                        return await _exec()
            elif _limiter:
                async with _limiter:
                    return await _exec()
            elif _semaphore:
                async with _semaphore:
                    return await _exec()
            else:
                return await _exec()

        try:
            registry.active_tasks.add(id(asyncio.current_task()))
            if retries > 0:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(retries),
                    wait=wait_exponential_jitter(initial=0.2, max=2.0),
                    reraise=True,
                ):
                    with attempt:
                        res = await (
                            asyncio.wait_for(_invoke(), timeout=timeout)
                            if timeout
                            else _invoke()
                        )
            else:
                res = await (
                    asyncio.wait_for(_invoke(), timeout=timeout)
                    if timeout
                    else _invoke()
                )

            registry.record_success()
            return res
        except Exception:
            registry.record_error()
            source.is_healthy = False
            source.last_check_time = datetime.now()
            raise
        finally:
            registry.active_tasks.discard(id(asyncio.current_task()))

    def configure(
        self,
        weight: Optional[float] = None,
        max_requests_per_minute: Optional[int] = None,
        max_concurrent: Optional[int] = None,
    ):
        """配置所有实现的方法参数"""
        for _, registry in self.implementations:
            if weight is not None:
                registry.update_weight(weight)
            if max_requests_per_minute is not None or max_concurrent is not None:
                registry.update_limits(max_requests_per_minute, max_concurrent)

    def configure_for_source(
        self,
        source_name: DataSourceName,
        weight: Optional[float] = None,
        max_requests_per_minute: Optional[int] = None,
        max_concurrent: Optional[int] = None,
    ):
        """为特定数据源配置方法参数"""
        for source, registry in self.implementations:
            if source.name == source_name:
                if weight is not None:
                    registry.update_weight(weight)
                if max_requests_per_minute is not None or max_concurrent is not None:
                    registry.update_limits(max_requests_per_minute, max_concurrent)
                return
        raise ValueError(f"未找到数据源 {source_name} 的方法实现")


class DataSourceManager:
    """数据源管理器"""

    def __init__(self):
        self.data_sources: Dict[DataSourceName, StockDataSource] = {}
        self.service_methods: Dict[str, ServiceMethod] = {}
        self.health_check_interval = 300  # 每5分钟检查一次

    def register_data_source(self, source_cls: Type[T]) -> Type[T]:
        """类装饰器：注册数据源类"""
        source_name = source_cls.name
        if source_name in self.data_sources:
            raise ValueError(f"数据源 {source_name} 已经注册")

        instance = source_cls()
        self.data_sources[source_name] = instance
        logger.info(f"注册数据源: {source_name.value} ({source_cls.__name__})")
        return source_cls

    def register_method(
        self,
        weight: float = 1.0,
        max_requests_per_minute: Optional[int] = None,
        max_concurrent: Optional[int] = None,
    ):
        def decorator(func: Callable):
            method_name = func.__name__

            if method_name not in self.service_methods:
                self.service_methods[method_name] = ServiceMethod(method_name, self)

            registry = MethodRegistry(func, weight)
            registry.update_limits(max_requests_per_minute, max_concurrent)

            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 仅透传原函数调用，不做限流/统计/健康检查
                return await func(*args, **kwargs)

            def register_implementation(instance):
                self.service_methods[method_name].add_implementation(instance, registry)

            wrapper._delayed_registration = partial(register_implementation)
            return wrapper

        return decorator

    def complete_registration(self):
        """完成所有方法的注册（在数据源实例化后调用）"""
        for source in self.data_sources.values():
            for attr_name in dir(source):
                attr = getattr(source, attr_name)
                # 既可能是函数，又可能是绑定方法，_delayed_registration 在函数对象上
                delayed = getattr(attr, "_delayed_registration", None)
                if delayed is None and hasattr(attr, "__func__"):
                    delayed = getattr(attr.__func__, "_delayed_registration", None)
                if callable(attr) and delayed:
                    delayed(source)

    def configure_method(
        self,
        method_name: str,
        weight: Optional[float] = None,
        max_requests_per_minute: Optional[int] = None,
        max_concurrent: Optional[int] = None,
    ):
        """配置方法参数（所有实现）"""
        if method_name not in self.service_methods:
            raise ValueError(f"未注册的服务方法: {method_name}")
        self.service_methods[method_name].configure(
            weight, max_requests_per_minute, max_concurrent
        )

    def configure_method_for_source(
        self,
        method_name: str,
        source_name: DataSourceName,
        weight: Optional[float] = None,
        max_requests_per_minute: Optional[int] = None,
        max_concurrent: Optional[int] = None,
    ):
        """为特定数据源配置方法参数"""
        if method_name not in self.service_methods:
            raise ValueError(f"未注册的服务方法: {method_name}")
        self.service_methods[method_name].configure_for_source(
            source_name, weight, max_requests_per_minute, max_concurrent
        )

    async def is_healthy(self, source_name: DataSourceName) -> bool:
        """检查数据源健康状态，必要时执行健康检查"""
        source = self.data_sources.get(source_name)
        if not source:
            return False

        # 检查是否需要执行健康检查
        last_check = source.last_check_time
        needs_check = last_check is None or (datetime.now() - last_check) > timedelta(
            seconds=self.health_check_interval
        )

        if needs_check or not source.is_healthy:
            try:
                source.is_healthy = await source.health_check()
                source.last_check_time = datetime.now()
                status = "健康" if source.is_healthy else "不健康"
                logger.info(f"健康检查完成: {source_name.value} -> {status}")
            except Exception as e:
                source.is_healthy = False
                logger.error(f"健康检查失败 [{source_name.value}]: {str(e)}")

        return source.is_healthy

    def get_source(self, source_name: DataSourceName) -> StockDataSource:
        """获取数据源实例"""
        source = self.data_sources.get(source_name)
        if not source:
            raise ValueError(f"未注册的数据源: {source_name}")
        return source

    def get_method(self, method_name: str) -> ServiceMethod:
        """获取服务方法接口"""
        if method_name not in self.service_methods:
            raise ValueError(f"未注册的服务方法: {method_name}")
        return self.service_methods[method_name]

    def get_method_stats(self, method_name: str) -> List[dict]:
        """获取方法统计信息"""
        if method_name not in self.service_methods:
            raise ValueError(f"未注册的服务方法: {method_name}")
        return [
            reg.get_stats()
            for _, reg in self.service_methods[method_name].implementations
        ]

    def bind(self, protocol_cls: type) -> Any:
        """
        根据给定 Protocol 生成一个代理对象：
        - 代理暴露的可调用方法集合 = Protocol 中定义的可调用属性
        - 每个代理方法调用时，动态选择最佳数据源实现并转发到 ServiceMethod.call()
        - 为了 IDE 友好，代理方法挂载首个实现的 __signature__ 与 __doc__
        - 允许通过关键字透传特殊调用项：limiter、semaphore、timeout、retries
        （这些名字若出现在 kwargs 中会被提取并传给 ServiceMethod.call）
        """
        # 1) 取出 Protocol 中的方法契约（只选可调用且非私有）
        protocol_members = {
            name: obj
            for name, obj in vars(protocol_cls).items()
            if callable(obj) and not name.startswith("_")
        }
        if not protocol_members:
            raise ValueError(
                f"{protocol_cls.__name__} 未定义任何可调用方法（Protocol 空壳？）"
            )

        # 2) 确认这些方法都已在 manager 中注册
        missing = [
            name for name in protocol_members.keys() if name not in self.service_methods
        ]
        if missing:
            raise ValueError(
                f"以下方法尚未注册到 DataSourceManager: {', '.join(missing)}"
            )

        proxy = SimpleNamespace()  # 简洁：实例属性直接赋函数即可（不需要 self 绑定）

        # 3) 为每个方法构造一个异步代理函数
        for method_name in protocol_members.keys():
            service_method = self.service_methods[method_name]

            # 给 IDE 的签名与文档：取首个实现的方法签名/文档（若存在）
            impl_sig = None
            impl_doc = None
            for src, _reg in service_method.implementations:
                try:
                    bound = getattr(src, method_name)
                    impl_sig = inspect.signature(bound)
                    impl_doc = getattr(bound, "__doc__", None)
                    break
                except Exception:
                    continue

            async def _caller(*args, _method_name=method_name, **kwargs):
                # 把特殊调用参数剥离并传入 ServiceMethod.call（不污染真实业务参数）
                special = {}
                for k in ("limiter", "semaphore", "timeout", "retries"):
                    if k in kwargs:
                        special[k] = kwargs.pop(k)
                return await self.get_method(_method_name).call(
                    *args, **special, **kwargs
                )

            # 挂上名字/签名/文档，提升开发体验
            _caller.__name__ = method_name
            if impl_doc:
                _caller.__doc__ = impl_doc
            if impl_sig is not None:
                # 将真实实现签名暴露到代理，IDE/inspect 会使用它
                _caller.__signature__ = impl_sig

            setattr(proxy, method_name, _caller)

        return proxy

    async def stat(self) -> dict:
        """返回包含所有数据源和方法的可序列化监控信息"""
        # 收集数据源状态
        data_sources = {}
        for name, source in self.data_sources.items():
            data_sources[name.value] = {
                "is_healthy": await source.health_check(),
                "last_check_time": (
                    source.last_check_time.isoformat()
                    if source.last_check_time
                    else None
                ),
                # 可扩展其他数据源特定指标
            }

        # 收集方法统计
        methods = {}
        for method_name, service_method in self.service_methods.items():
            method_stats = []
            for _, registry in service_method.implementations:
                stats = registry.get_stats()
                # 转换日期时间为字符串
                if stats["last_call_time"]:
                    stats["last_call_time"] = stats["last_call_time"].isoformat()
                # 移除非序列化字段并保留必要信息
                method_stats.append(
                    {
                        "data_source": stats["data_source"],
                        "active_tasks": stats["active_tasks"],
                        "call_count": stats["call_count"],
                        "error_count": stats["error_count"],
                        "success_rate": stats["success_rate"],
                        "last_call_time": stats["last_call_time"],
                        "weight": stats["weight"],
                        "qps_limit": stats["qps_limit"],
                        "concurrent_limit": stats["concurrent_limit"],
                    }
                )
            methods[method_name] = method_stats

        return {
            "data_sources": data_sources,
            "methods": methods,
        }


# 管理器单例
manager = DataSourceManager()


class DataSourceUnavailableError(Exception):
    """数据源不可用异常"""

    def __init__(self, source_name: Union[DataSourceName, str]):
        if isinstance(source_name, DataSourceName):
            message = f"数据源不可用: {source_name.value}"
        else:
            message = source_name
        super().__init__(message)
