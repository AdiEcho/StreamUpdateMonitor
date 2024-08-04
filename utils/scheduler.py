import os
from loguru import logger
from utils.config import config
from urllib.parse import quote_plus
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.background import BackgroundScheduler

if config.scheduler.enable:
    bs_config = {
        'apscheduler.executors.default': {
            'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
            'max_workers': '20'
        },
        'apscheduler.executors.processpool': {
            'type': 'processpool',
            'max_workers': '5'
        },
        'apscheduler.job_defaults.max_instances': '50',
    }
    for store in config.scheduler.store:
        if store.store_backend == "sqlite" and store.store_enable:
            # it seems that need to dump the model first, is this correct?
            sqlite_url = f'sqlite:///{store.config.model_dump().get("db_path", "").replace(os.sep, "/")}'
            bs_config["apscheduler.jobstores.default"] = {
                'type': 'sqlalchemy',
                'url': sqlite_url
            }
        elif store.store_backend == "mysql" and store.store_enable:
            config = store.config.model_dump()
            mysql_url = f"mysql+pymysql://{config.get('user')}:{quote_plus(config.get('password'))}@{config.get('host')}:" \
                        f"{config.get('port')}/{config.get('db')}?charset=utf8mb4"
            bs_config["apscheduler.jobstores.default"] = {
                'type': 'sqlalchemy',
                'url': mysql_url
            }
        else:
            logger.info("Scheduler store is disabled. Will not store jobs.")

    scheduler = BackgroundScheduler(bs_config)
else:
    logger.warning("Scheduler is disabled. Will run once and quite.")
    scheduler = None

if scheduler:
    scheduler.start()


def add_job(func, trigger, **kwargs):
    if kwargs.get("name"):
        name = kwargs.get("name")
    else:
        name = f"{kwargs.get('kwargs', {}).get('_service', '').__class__.__name__}"

    job = scheduler.get_job(name)
    if job:
        if isinstance(trigger, IntervalTrigger) and isinstance(job.trigger, IntervalTrigger):
            if trigger.interval == job.trigger.interval:
                logger.info(f'Job {name} already exists with the same interval, skipping')
                return
            else:
                logger.info(f'Job {name} already exists with different interval, rescheduling')
                job.modify(trigger=trigger)
        elif isinstance(trigger, DateTrigger) and isinstance(job.trigger, DateTrigger):
            if trigger.run_date == job.trigger.run_date:
                logger.info(f'Job {name} already exists with the same run date, skipping')
                return
            else:
                logger.info(f'Job {name} already exists with different run date, rescheduling')
                job.modify(trigger=trigger)
        else:
            logger.info(f'Job {name} exists with different trigger type, rescheduling')
            job.modify(trigger=trigger)
    else:
        scheduler.add_job(func, trigger, id=name, **kwargs)
        logger.info(
            f'Added job {func.__name__}({kwargs.get("kwargs", {}).get("_service", "").__class__.__name__}) with trigger {trigger}')