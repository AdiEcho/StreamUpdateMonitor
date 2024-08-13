import sys
import time
from utils import sql
from loguru import logger
from datetime import datetime
from utils.config import config
from services import Service_T, ServiceMap
from utils.scheduler import scheduler, add_job
from sqlalchemy.orm.session import sessionmaker
from apscheduler.triggers.date import DateTrigger
from notification import Notification_T, NotificationMap
from apscheduler.triggers.interval import IntervalTrigger

if sys.flags.debug or sys.gettrace():
    import utils.debug_log


def init_services() -> list[Service_T]:
    """
    Initialize services base on config
    :return:
    """
    service_list = []
    for service_name, service_setting in config.services.items():
        if not service_setting.enable:
            continue
        if service_name.lower() not in ServiceMap:
            logger.warning(f"Service {service_name} not found")
            continue
        service_list.append(ServiceMap[service_name](service_setting))
    return service_list


def init_database() -> list[sessionmaker]:
    """
    Initialize database
    :return:
    """
    db_list = []
    if not config.db:
        return db_list
    for db in config.db:
        if not db.enable:
            continue
        engine = sql.create_service_engine(db.type, db.config)
        sql.create_db(engine)
        db_list.append(sql.get_session_factory(engine))
    return db_list


def init_notification() -> list[Notification_T]:
    """
    Initialize notifications
    :return:
    """
    notification_list = []
    for notification in config.notifications:
        if not notification.enable:
            continue
        if notification.type.lower() not in NotificationMap:
            logger.warning(f"Notification {notification.type} not found")
            continue
        n = NotificationMap[notification.type.lower()](notification.config)
        n.configuration(config=notification.config)
        notification_list.append(n)
    return notification_list


def monitor_service(_service: Service_T):
    """
    Monitor service
    :param _service:
    :return:
    """
    notification_list = [hash(x.__class__.__name__) for x in __notifications]
    db_list = [hash(x.kw.get("bind").url) for x in __dbs]
    _service.request(notification_list=notification_list, db_list=db_list)
    if len(__notifications) > 0:
        for n in __notifications:
            for msg in _service.get_notification_msgs(msg_format=n.config.get("msg_format", "text"), notification_obj=n):
                if n.config.get("immediate_send"):
                    if n.send_msg(msg):
                        logger.info(f"Send notification success")
                    else:
                        logger.error(f"Send notification failed")
                else:
                    if msg.send_time < datetime.now():
                        logger.error("Send time is earlier than now, will not send")
                        continue
                    if n.config.get("update_send_time"):
                        _trigger = DateTrigger(run_date=msg.send_time.replace(hour=0, minute=0, second=0, microsecond=0))
                    else:
                        _trigger = DateTrigger(run_date=msg.send_time)
                    add_job(n.send_msg, _trigger, kwargs={"msg": msg}, name=msg.name)
    if len(__dbs) > 0:
        for session_maker in __dbs:
            session = session_maker()
            queries = _service.get_sql_query(session)
            for q in queries:
                session.add(q)
            session.commit()
            session.close()


# init services
__services = init_services()
if len(__services) == 0:
    logger.error("No services enabled, will exit")
    exit(1)
# init database
__dbs = init_database()
if len(__dbs) == 0:
    logger.error("No database enabled, will not save data")
# init notification
__notifications = init_notification()
if len(__notifications) == 0:
    logger.error("No notification enabled, will not send notification")


# run once
for service in __services:
    monitor_service(_service=service)

# start scheduler
if config.scheduler.enable:
    for service in __services:
        trigger = IntervalTrigger(minutes=service.config.interval)
        add_job(monitor_service, trigger, kwargs={"_service": service})
    logger.info("Scheduler started")
    while True:
        if not scheduler.running:
            logger.error("Scheduler stopped, will exit")
            break
        scheduler.print_jobs()  # print jobs for debug
        time.sleep(3600)
else:
    logger.info("Scheduler is disabled. Run once and quite.")
