from src.crud.order import OrderCRUD, OrderItemCRUD
from src.crud.product import ProductCRUD
from src.models.models import Nomenclature, OrderItem
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

    async def get_orderitem_to_update(
        self,
        order_item_crud: OrderItemCRUD,
        order_crud: OrderCRUD,
        product: Nomenclature,
    ) -> OrderItem:
        order_item = await order_item_crud.get_by(
            order_id=self.order_id, nomenclature_id=self.nomenclature_id
        )
        order = await order_crud.get_by(id=self.order_id)
        return (
            await order_item_crud.create(
                CreateOrder(
                    amount=self.amount,
                    order_id=self.order_id,
                    nomenclature_id=self.nomenclature_id,
                    price=product.price,
                    created_at=order.created_at,
                )
            )
            if not order_item
            else order_item
        )

    async def update_orderitem(
        self,
    ) -> OrderOut | NotInStockExceptionError | ProductNotFoundExceptionError:
        """
        Обновление количества товара в заказе:

        1. Проверка наличия товара
        2. Получение объекта заказ-товар из БД или создание нового
        3. Обновление количества товара в объекте заказ-товар
        4. Обновление количества товара в БД

        """
        product = await ProductService(self.nomenclature_id).check_amount(self.amount)
        async with (
            OrderItemCRUD() as order_item_crud,
            OrderCRUD() as order_crud,
            ProductCRUD() as product_crud,
        ):
            db_order_item = await self.get_orderitem_to_update(
                order_item_crud=order_item_crud, order_crud=order_crud, product=product
            )
            new_order_item = UpdateOrder(
                order_id=db_order_item.order_id,
                nomenclature_id=db_order_item.nomenclature_id,
                amount=self.amount + db_order_item.amount,
            )
            created_order_item = await order_item_crud.update(
                db_order_item, new_order_item
            )
            await product_crud.update(
                product.id, {"amount": product.amount - self.amount}
            )
            return OrderOut.model_validate(created_order_item)
