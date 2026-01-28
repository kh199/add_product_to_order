from src.crud.product import ProductCRUD
from src.models.models import Nomenclature
from src.tools.exceptions import NotInStockExceptionError, ProductNotFoundExceptionError


class ProductService:
    def __init__(self, nomenclature_id: int):
        self.nomenclature_id = nomenclature_id

    async def check_product(self) -> Nomenclature | ProductNotFoundExceptionError:
        async with ProductCRUD() as crud:
            product = await crud.get_by(id=self.nomenclature_id)
            if not product:
                raise ProductNotFoundExceptionError
            return product

    async def check_amount(
        self, amount: int
    ) -> Nomenclature | NotInStockExceptionError:
        product = await self.check_product()
        if product.amount < amount:
            raise NotInStockExceptionError
        return product
