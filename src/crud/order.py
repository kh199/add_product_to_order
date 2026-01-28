from src.crud.base import DBBase, ModelType
from src.models.models import OrderItem


class OrderItemCRUD(DBBase):
    def __init__(self, model: type[ModelType] = OrderItem) -> None:
        super().__init__(model=model)
