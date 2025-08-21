from .scheduler import task_scheduler
from sqlalchemy.ext.asyncio import AsyncSession
from .stock_basic_task import update_stock_basic_info
from .stock_daily_task import update_stock_daily

def init_scheduler_tasks(session:AsyncSession):

    task_scheduler.add_task(
        func=update_stock_basic_info,
        cron="0 0 * * *",  # 每天0点执行一次
        task_id="update_stock_basic_info_task",
        run_on_start=True,
        session=session,
    )

    task_scheduler.add_task(
        func=update_stock_daily,
        cron="0 16 * * 1-5",  # 每天16点执行一次
        task_id="update_stock_daily_task",
        run_on_start=True,
        session=session,
    )

    return task_scheduler
