import os
import sys
import yaml
import traceback
from pathlib import Path
from loguru import logger
from typing import Optional, Union
from pydantic import BaseModel, Field, ValidationError, field_serializer


class Directories:
    def __init__(self):
        self.package_root = Path(__file__).resolve().parent.parent
        self.configuration = self.package_root / "config"
        self.logs = self.package_root / "logs"


d = Directories()


class DBConfig(BaseModel):
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=3306, description="Database port")
    db: str = Field(default="", description="Database name")
    user: str = Field(default="", description="Database user")
    password: str = Field(default="", description="Database password")


class SQLiteConfig(BaseModel):
    db_path: str = Field(default=f"{d.configuration}/sqlite.db", description="SQLite file abs path")

    @field_serializer('db_path')
    def no_args(self, v):
        if v is None or v == "":
            return f"{d.configuration}/sum.db"
        return v


class DB(BaseModel):
    enable: bool = Field(default=False, description="Enable database")
    type: str = Field(default="sqlite", description="Database type")
    config: Union[DBConfig, SQLiteConfig] = Field(default_factory=dict, description="Database extra configuration")


class Notification(BaseModel):
    enable: bool = Field(default=False, description="Enable notifications")
    type: str = Field(default="", description="Notification type")
    config: dict = Field(default_factory=dict, description="Notification extra configuration")


class SchedulerStore(BaseModel):
    store_enable: bool = Field(default=False, description="Enable scheduler store")
    store_backend: str = Field(default="sqlite", description="Scheduler store type")
    config: Union[DBConfig, SQLiteConfig] = Field(default=dict, description="Scheduler store extra configuration")


class Scheduler(BaseModel):
    enable: bool = Field(default=False, description="Enable scheduler")
    store: list[SchedulerStore] = Field(default_factory=list, description="Scheduler store configuration")


class Service(BaseModel):
    enable: bool = Field(default=False, description="Enable service update monitoring")
    interval: int = Field(default=60, description="Service update interval, in minutes")
    immediate_send: bool = Field(default=False, description="Send notification immediately on update")
    extra_config: dict = Field(default_factory=dict, description="Service extra configuration")


class Config(BaseModel):
    log: dict = Field(default="info", description="Logging level")
    headers: dict = Field(default_factory=dict, description="Default headers")
    db: list[DB] = Field(default_factory=list, description="Database configuration")
    notifications: list[Notification] = Field(default_factory=list, description="Notification configuration")
    scheduler: Scheduler = Field(default_factory=Scheduler, description="Scheduler configuration")
    services: dict[str, Service] = Field(default_factory=dict, description="Service configuration")

    class Config:
        extra = "forbid"

    class LogConfig:
        level: str = "info"
        sink: str = "logs/app.log"
        rotation: str = "1 week"
        retention: str = "1 month"


def load_config(file_path: str) -> Config:
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    return Config(**data)


def configure_logger(_config: Config):
    log_config = _config.log
    log_enable = log_config.get("enable", False)
    std_level = log_config.get('std_level', 'DEBUG')
    if log_enable:
        log_level = log_config.get('log_level', 'DEBUG')
        log_rotation = log_config.get('rotation', '1 MB')
        log_retention = log_config.get('retention', '15 days')

        os.makedirs(d.logs, exist_ok=True)
        logger.remove()
        logger.add(sys.stdout, level=std_level)  # 控制台输出
        logger.add(
            os.path.join(d.logs, 'SUM.log'),
            level=log_level,
            rotation=log_rotation,
            retention=log_retention
        )


try:
    config = load_config(os.path.join(d.configuration, 'config.yaml'))
    configure_logger(config)
    logger.info(f"Configuration loaded: {config.model_dump_json()}")
except ValidationError as e:
    logger.error(f"Configuration error: {e}")
except Exception as e:
    if sys.gettrace():
        traceback.print_exc()
    logger.error(f"Failed to load configuration file: {e}")
