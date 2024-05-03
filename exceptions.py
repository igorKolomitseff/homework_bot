class SendMessageError(Exception):
    """Класс исключения для обработки ошибок во время отправки сообщения."""


class StatusCodeIsNot200Error(Exception):
    """Класс исключения для обработки ошибок во время запроса к API."""


class UnavailableAPIError(Exception):
    """Класс исключения для обработки ошибки недоступности API-сервиса."""
