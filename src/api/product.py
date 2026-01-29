from fastapi import APIRouter, status

from src.schemas.order import OrderOut, UpdateOrder
from src.services.order import OrderService
from src.tools.exception_route import ExceptionHandlingRoute

router = APIRouter(
    prefix="/orders", tags=["Orders"], route_class=ExceptionHandlingRoute
)


@router.post(
    "/add_product",
    summary="Добавить товар в заказ",
    status_code=status.HTTP_200_OK,
    response_model=OrderOut,
)
async def add_product_to_order(order: UpdateOrder):
    return await OrderService(**order.model_dump()).update_orderitem()
