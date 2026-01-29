from sqlalchemy import func, select

from src.crud.base import DBBase, ModelType
from src.models.models import Customer, Order, OrderItem
from src.schemas.order import UpdateOrder


class OrderItemCRUD(DBBase):
    def __init__(self, model: type[ModelType] = OrderItem) -> None:
        super().__init__(model=model)

    async def get_order_sum(self) -> int:
        """Получение информации о сумме товаров заказанных для каждого клиента."""
        query = await self.session.execute(
            select(
                Customer.name,
                func.coalesce(func.sum(OrderItem.amount * OrderItem.price), 0),
            )
            .join(Order, Order.customer_id == Customer.id, isouter=True)
            .join(OrderItem, Order.id == OrderItem.order_id, isouter=True)
            .group_by(Customer.id)
        )
        return query.scalars().all()

    async def update(
        self,
        db_obj: OrderItem,
        obj_in: UpdateOrder,
    ) -> Order:
        obj_in = obj_in.model_dump()
        for field, value in obj_in.items():
            if value is not None and field in db_obj.to_dict():
                setattr(db_obj, field, value)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj


class OrderCRUD(DBBase):
    def __init__(self, model: type[ModelType] = Order) -> None:
        super().__init__(model=model)
