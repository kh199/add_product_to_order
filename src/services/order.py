from src.crud.order import OrderItemCRUD
from src.models.models import OrderItem
from src.schemas.order import CreateOrder, OrderOut, UpdateOrder
from src.services.product import ProductService
from src.tools.exceptions import NotInStockExceptionError, ProductNotFoundExceptionError


class OrderService:
    def __init__(
        self,
        nomenclature_id: int,
        order_id: int,
        amount: str,
    ):
        self.nomenclature_id = nomenclature_id
        self.order_id = order_id
        self.amount = amount

    async def get_orderitem_to_update(self) -> OrderItem:
        async with OrderItemCRUD() as crud:
            order_item = await crud.get_by(
                id=self.order_id, nomenclature_id=self.nomenclature_id
            )
            if not order_item:
                order_item = await crud.create(
                    CreateOrder(
                        amount=self.amount,
                        id=self.order_id,
                        nomenclature_id=self.nomenclature_id,
                    )
                )
            return order_item

    async def update_orderitem(
        self,
    ) -> OrderOut | NotInStockExceptionError | ProductNotFoundExceptionError:
        await ProductService(self.nomenclature_id).check_amount(self.amount)
        db_order_item = await self.get_orderitem_to_update()
        new_order_item = UpdateOrder(
            id=db_order_item.id,
            nomenclature_id=db_order_item.nomenclature_id,
            amount=self.amount + db_order_item.amount,
        )
        async with OrderItemCRUD() as crud:
            created_order_item = await crud.update(db_order_item, new_order_item)
            return OrderOut.model_validate(created_order_item)
