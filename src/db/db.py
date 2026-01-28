from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
    sessionmaker,
)
from sqlalchemy.pool import NullPool

from src.core.config import settings


class Base(DeclarativeBase):
    """
    Базовый класс для наследования моделей в проекте.

    Автоинкремент названия таблицы в бд через
    cls.__name__.lower()
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa: N805
        return cls.__name__.lower()

    def to_dict(self) -> dict:
        """
        Преобразование модели в словарь.
        """
        return self.__dict__

    def __repr__(self) -> str:
        """
        Переопределение метода __repr__ для моделей.
        """
        return f"<{self.__class__.__name__} {self.to_dict()}>"

    def from_dict(self, data: dict):
        for field in data:
            if hasattr(self, field):
                setattr(self, field, data[field])


class IntegerIdMixin:
    """
    Миксин для добавления в таблицы БД поля id типа Integer и даты создания записи.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата создания записи",
    )


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


engine = create_async_engine(settings.database_url, poolclass=NullPool)
async_session = sessionmaker(engine, class_=AsyncSession)
