class CustomExceptionError(Exception):
    """Базовый класс для всех исключений приложения.

    Attributes:
        message (str): Сообщение об ошибке.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        """Возвращает сообщение об ошибке."""
        return f"{self.message}"


class UserNotFoundExceptionError(CustomExceptionError):
    """Класс для исключений, если пользователь не найден."""

    def __init__(self, message="Пользователь не найден"):
        super().__init__(message)


class ObjectNotFoundExceptionError(CustomExceptionError):
    """Класс для исключений, если объект не найден."""

    def __init__(self, message="Объект не найден"):
        super().__init__(message)


class ProductNotFoundExceptionError(CustomExceptionError):
    """Класс для исключений, если товар не найден."""

    def __init__(self, message="Товар не найден"):
        super().__init__(message)


class NotInStockExceptionError(CustomExceptionError):
    """Класс для исключений, если товара недостаточно для заказа."""

    def __init__(self, message="Недостаточно товара"):
        super().__init__(message)


class BadRequestExceptionError(CustomExceptionError):
    """Класс для исключений, если запрос неверный."""

    def __init__(self, message="Неверный запрос"):
        super().__init__(message)


class ClientConnectionError(CustomExceptionError):
    """Класс для исключений, если не удалось установить соединение."""

    def __init__(self, message="Ошибка соединения"):
        super().__init__(message)
