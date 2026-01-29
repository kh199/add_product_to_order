from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class Order(BaseModel):
    order_id: int
    nomenclature_id: int
    amount: int

    class Config:
        from_attributes = True


class CreateOrder(Order):
    created_at: datetime
    price: Decimal


class UpdateOrder(Order):
    pass


class OrderOut(Order):
    pass
