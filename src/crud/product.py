from src.crud.base import DBBase, ModelType
from src.models.models import Nomenclature


class ProductCRUD(DBBase):
    def __init__(self, model: type[ModelType] = Nomenclature) -> None:
        super().__init__(model=model)
