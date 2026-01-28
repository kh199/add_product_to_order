from fastapi import APIRouter, status

from src.schemas.order import OrderOut, UpdateOrder
from src.services.order import OrderService

router = APIRouter(prefix="/orders")


@router.post(
    "/add_product",
    summary="Добавить товар в заказ",
    status_code=status.HTTP_201_CREATED,
    response_model=OrderOut,
)
async def add_product_to_order(order: UpdateOrder):
    await OrderService(**order.model_dump()).update_orderitem()
