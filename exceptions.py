class NoTokensError(Exception):
    """Класс исключения для обработки ошибок проверки переменных окружения."""


class StatusCodeIsNot200Error(Exception):
    """Класс исключения для обработки ошибок во время запроса к API."""


class ErrorKeyInResponseError(Exception):
    """Класс исключения для обработки наличия ключа ошибки в ответе API."""
