import os
from typing import Union
from loguru import logger
from datetime import datetime
from urllib.parse import quote_plus
from sqlalchemy import String, DateTime, INT
from utils.config import DBConfig, SQLiteConfig
from sqlalchemy import create_engine, func, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker


def create_service_engine(backend: str, db_config: Union[DBConfig, SQLiteConfig]):
    if backend == "mysql":
        config = db_config.model_dump()
        __sql_url = f"mysql+pymysql://{config.get('user')}:{quote_plus(config.get('password'))}@{config.get('host')}:" \
                    f"{config.get('port')}/{config.get('db')}?charset=utf8mb4"
        return create_engine(__sql_url, echo=False)
    elif backend == "sqlite":
        __sql_url = f'sqlite:///{db_config.model_dump().get("db_path", "").replace(os.sep, "/")}'
        return create_engine(__sql_url, echo=False)


class Base(DeclarativeBase):
    pass


class ServiceBase(Base):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(255), nullable=True)
    image: Mapped[str] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True, comment="release name")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=func.now(), comment="column create time")
    release_time: Mapped[datetime] = mapped_column(DateTime, nullable=True, comment="stream release time")


class NetflixSQL(ServiceBase):
    __tablename__ = 'netflix_service'
    video_id: Mapped[int] = mapped_column(INT, nullable=True, comment="netflix title id")
    genre: Mapped[str] = mapped_column(INT, nullable=True, comment="genre id")
    collection: Mapped[str] = mapped_column(INT, nullable=True, comment="collection id")
    country: Mapped[str] = mapped_column(String(255), nullable=True, comment="country name, seems that always US")

    def __repr__(self):
        return f"Netflix({self.name!r}->{self.release_time!r})"


def create_db(engine):
    if not engine:
        logger.error("No engine provided")
        return
    service_sql_classes = [NetflixSQL]

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    for s in service_sql_classes:
        if s.__tablename__ not in tables:
            Base.metadata.create_all(engine)


def get_session(engine):
    if not engine:
        return
    return Session(bind=engine)


def get_session_factory(engine):
    if not engine:
        return
    return sessionmaker(bind=engine)


if __name__ == '__main__':
    ...
