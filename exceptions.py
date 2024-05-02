class SendMessageError(Exception):
    """Класс исключения для обработки ошибок во время отправки сообщения."""

    pass


class StatusCodeIsNot200Error(Exception):
    """Класс исключения для обработки ошибок во время запроса к API."""

    pass


class UnavailableAPIError(Exception):
    """Класс исключения для обработки ошибки недоступности API-сервиса."""

    pass
