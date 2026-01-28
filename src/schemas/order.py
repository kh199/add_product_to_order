from pydantic import BaseModel


class Order(BaseModel):
    order_id: int
    nomenclature_id: int


class CreateOrder(Order):
    amount: int

    class Config:
        orm_mode = True


class UpdateOrder(CreateOrder):
    pass


class OrderOut(CreateOrder):
    pass
