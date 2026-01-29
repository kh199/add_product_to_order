from functools import wraps

from fastapi import HTTPException, status
from fastapi.routing import APIRoute

from src.tools.exceptions import (
    ClientConnectionError,
    NotInStockExceptionError,
    ObjectNotFoundExceptionError,
    ProductNotFoundExceptionError,
    UserNotFoundExceptionError,
)


def handle_exceptions(route_func):
    @wraps(route_func)
    async def wrapper(*args, **kwargs):
        try:
            return await route_func(*args, **kwargs)
        except TypeError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
        except UserNotFoundExceptionError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except ObjectNotFoundExceptionError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except ProductNotFoundExceptionError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except NotInStockExceptionError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except ClientConnectionError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
            )

    return wrapper


class ExceptionHandlingRoute(APIRoute):
    def get_route_handler(self):
        original_route_handler = super().get_route_handler()
        return handle_exceptions(original_route_handler)
