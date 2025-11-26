import asyncio
import inspect
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

# 配置混合执行器
executors = {
    "async": AsyncIOExecutor(),  # 异步执行器
    "thread": ThreadPoolExecutor(10),  # 线程池执行器（用于同步任务）
}


class TaskScheduler:
    def __init__(self, url: str, use_async: bool = False):
        """
        初始化任务调度器

        :param use_async: 是否使用异步调度器
        """
        url = url.replace("+asyncpg", "")
        url = url.replace("+aiosqlite", "")
        # 配置调度器
        jobstores = {"default": SQLAlchemyJobStore(url)}

        if use_async:
            # 异步调度器
            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores, executors=executors, timezone="Asia/Shanghai"
            )
            self._is_async = True
        else:
            # 同步调度器
            self.scheduler = BackgroundScheduler(
                jobstores=jobstores,
                executors={"default": ThreadPoolExecutor(20)},
                timezone="Asia/Shanghai",
            )
            self._is_async = False

        self._running = False

    def start(self):
        """启动调度器"""
        if not self._running:
            if self._is_async:
                # 异步调度器需要在事件循环中启动
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 如果事件循环正在运行，使用call_soon_threadsafe
                        loop.call_soon_threadsafe(self.scheduler.start)
                    else:
                        # 否则直接启动
                        loop.run_until_complete(self.scheduler.start())
                except RuntimeError:
                    # 没有事件循环，创建一个新的
                    asyncio.run(self.scheduler.start())
            else:
                # 同步调度器直接启动
                self.scheduler.start()

            self._running = True
            logger.info(f"Task scheduler started at {datetime.now()}")

    def shutdown(self):
        """关闭调度器"""
        if self._running:
            if self._is_async:
                # 异步调度器需要在事件循环中关闭
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.call_soon_threadsafe(self.scheduler.shutdown)
                    else:
                        loop.run_until_complete(self.scheduler.shutdown())
                except RuntimeError:
                    asyncio.run(self.scheduler.shutdown())
            else:
                # 同步调度器直接关闭
                self.scheduler.shutdown(wait=True)

            self._running = False
            logger.info(f"Task scheduler stopped at {datetime.now()}")

    def add_task(
        self,
        func: Callable,
        cron: str,
        task_id: str,
        run_on_start: bool = False,
        replace_existing: bool = True,
        executor: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        添加定时任务

        :param func: 任务函数（同步或异步）
        :param cron: cron表达式
        :param task_id: 任务唯一标识
        :param run_on_start: 是否在启动时立即执行
        :param replace_existing: 是否替换已存在的任务
        :param executor: 指定执行器（'async'或'thread'），None表示自动选择
        :param kwargs: 传递给任务函数的参数
        """
        trigger = CronTrigger.from_crontab(cron)

        # 自动检测任务类型并选择执行器
        if executor is None:
            if inspect.iscoroutinefunction(func):
                executor = "async"
            else:
                executor = "thread"

        # 如果是异步任务但调度器是同步的，需要包装任务
        if executor == "async" and not self._is_async:
            # 将异步任务包装为同步任务
            func = self._wrap_async_task(func)
            executor = "thread"

        # 添加任务
        self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=task_id,
            replace_existing=replace_existing,
            executor=executor,
            kwargs=kwargs,
            misfire_grace_time=30,  # 允许延迟30秒执行
        )

        # 启动时立即执行
        if run_on_start:
            if executor == "async" and self._is_async:
                # 异步任务需要在事件循环中执行
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 如果事件循环正在运行，使用call_soon_threadsafe
                        loop.call_soon_threadsafe(
                            lambda: asyncio.create_task(func(**kwargs))
                        )
                    else:
                        # 否则直接运行
                        loop.run_until_complete(func(**kwargs))
                except RuntimeError:
                    asyncio.run(func(**kwargs))
            else:
                # 同步任务直接执行
                func(**kwargs)

        logger.info(f"Task '{task_id}' added with cron: {cron}, executor: {executor}")

    def _wrap_async_task(self, async_func: Callable) -> Callable:
        """将异步任务包装为同步任务"""

        @wraps(async_func)
        def wrapper(*args, **kwargs):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环正在运行，使用run_until_complete
                    return loop.run_until_complete(async_func(*args, **kwargs))
                else:
                    # 否则创建新的事件循环
                    return asyncio.run(async_func(*args, **kwargs))
            except Exception as e:
                logger.error(f"Error in async task wrapper: {e}")
                raise

        return wrapper

    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        try:
            self.scheduler.remove_job(task_id)
            logger.info(f"Task '{task_id}' removed")
            return True
        except Exception as e:
            logger.error(f"Failed to remove task '{task_id}': {e}")
            return False

    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        try:
            self.scheduler.pause_job(task_id)
            logger.info(f"Task '{task_id}' paused")
            return True
        except Exception as e:
            logger.error(f"Failed to pause task '{task_id}': {e}")
            return False

    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        try:
            self.scheduler.resume_job(task_id)
            logger.info(f"Task '{task_id}' resumed")
            return True
        except Exception as e:
            logger.error(f"Failed to resume task '{task_id}': {e}")
            return False

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        job = self.scheduler.get_job(task_id)
        if job:
            return {
                "id": job.id,
                "name": job.name,
                "next_run_time": (
                    job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
                    if job.next_run_time
                    else None
                ),
                "trigger": str(job.trigger),
                "executor": job.executor,
                "kwargs": job.kwargs,
            }
        return None

    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务信息"""
        jobs = {}
        for job in self.scheduler.get_jobs():
            jobs[job.id] = {
                "id": job.id,
                "name": job.name,
                "next_run_time": (
                    job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
                    if job.next_run_time
                    else None
                ),
                "trigger": str(job.trigger),
                "executor": job.executor,
                "kwargs": job.kwargs,
            }
        return jobs

    @contextmanager
    def task_context(self):
        """上下文管理器，用于临时启动/关闭调度器"""
        self.start()
        try:
            yield self
        finally:
            self.shutdown()

    @asynccontextmanager
    async def async_task_context(self):
        """异步上下文管理器，用于临时启动/关闭调度器"""
        self.start()
        try:
            yield self
        finally:
            self.shutdown()
