import requests
from loguru import logger
from typing import Optional
from datetime import datetime
from utils.config import config
from utils.sql import ServiceBase
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from requests.adapters import HTTPAdapter, Retry
from utils.config import Service as ServiceConfig


class DB(ABC):
    def __init__(self):
        self.client: Optional[type] = None

    def connect(self):
        ...

    def disconnect(self):
        ...

    def execute(self, query):
        ...


class Notification(ABC):
    def __init__(self, notification_config: dict):
        self.config = notification_config

    @abstractmethod
    def configuration(self, *args, **kwargs):
        ...

    @abstractmethod
    async def send_msg(self, *args, **kwargs):
        ...


class NotificationMSG(BaseModel):
    send_time: datetime = Field(default_factory=datetime.now, description="Notification send time")
    msg_format: str = Field(default="text", description="Notification message format")
    name: str = Field(default="", description="use for schedule, must be unique")
    title: str = Field(default="", description="Notification title")
    body: str = Field(default="", description="Notification body")
    tag: list[str] = Field(default_factory=list, description="Notification tags")


class Service(ABC):
    _session = None

    def __init__(self, _config):
        # is this necessary?
        # self.log = logger.bind(self.ALIASED[0])
        self.results = []
        self.config: ServiceConfig = _config

    @staticmethod
    def get_session() -> requests.Session:
        """
        Create a new session and add headers from config.
        :return:
        """
        if Service._session is None:
            Service._session = requests.Session()
            Service._session.mount("https://", HTTPAdapter(
                max_retries=Retry(
                    total=5,
                    backoff_factor=1,
                    status_forcelist=[429, 500, 502, 503, 504],
                )
            ))
            Service._session.hooks = {
                "response": lambda r, *_, **__: r.raise_for_status(),
            }
            Service._session.headers.update(config.headers)
        return Service._session

    @abstractmethod
    def request(self, *args, **kwargs):
        """
        Make a request to the service and save to self.results for further processing.
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def deduplication(self, *args, **kwargs):
        """
        Deduplicate the results.
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def get_notification_msgs(self, *args, **kwargs) -> list[NotificationMSG]:
        raise NotImplementedError

    @abstractmethod
    def get_sql_query(self, session, /, *args, **kwargs) -> list[ServiceBase]:
        raise NotImplementedError
