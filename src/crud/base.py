from abc import ABC, abstractmethod
from typing import Any, Generic, Sequence, Type, TypeVar

from loguru import logger
from pydantic import BaseModel
from sqlalchemy import Row, RowMapping, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.db import Base, async_session
from src.tools.exceptions import ObjectNotFoundExceptionError

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class DB(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self._model = model

    @abstractmethod
    async def get(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def create(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def update(self, *args, **kwargs):
        raise NotImplementedError


class DBBase(DB, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]) -> None:
        super().__init__(model=model)
        self.session: AsyncSession

    async def __aenter__(self):
        async with async_session() as session:
            self.session = session
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        self.session = None

    async def get(self) -> Sequence[Row | RowMapping | Any]:
        return (await self.session.scalars(select(self._model))).all()

    async def get_by(self, **kwargs) -> ModelType | None:
        stmt = select(self._model)
        for attr, value in kwargs.items():
            if value is not None:
                try:
                    stmt = stmt.where(getattr(self._model, attr) == value)
                except AttributeError:
                    logger.info(f"У модели {self._model} нет аттрибута {attr}")
                    continue
        return await self.session.scalar(stmt)

    async def create(self, db_obj: CreateSchemaType) -> ModelType | None:
        db_obj = self._model(**db_obj.model_dump())
        try:
            self.session.add(db_obj)
            await self.session.commit()
            await self.session.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as err:
            logger.error(err)
            await self.session.rollback()

    async def update(
        self,
        obj_id: int | str,
        obj_in: UpdateSchemaType | dict,
    ) -> ModelType:
        obj_in = obj_in if isinstance(obj_in, dict) else obj_in.model_dump()
        db_obj = await self.get_by(id=obj_id)
        if not db_obj:
            raise ObjectNotFoundExceptionError()
        for field, value in obj_in.items():
            if value is not None and field in db_obj.to_dict():
                setattr(db_obj, field, value)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj
