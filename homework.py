from http import HTTPStatus
import logging
import os
import sys
import time

import requests
from dotenv import load_dotenv
from telebot import TeleBot

from exceptions import (
    StatusCodeIsNot200Error
)


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

TOKENS = ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID')
NOT_TOKENS_ERROR = (
    'Отсутствуют обязательные переменные окружения: {tokens}.\n'
    'Программа принудительно остановлена.'
)
SEND_MESSAGE_SUCCESS = (
    'Сообщение успешно отправлено в Telegram.\n'
    'Текст сообщения: {message}'
)
SEND_MESSAGE_ERROR = (
    'Сообщение отправить в Telegram не удалось.\n'
    'Текст сообщения: {message}'
)
REQUEST_ERROR = (
    'Ошибка запроса к API-сервису Практикум Домашка.\n'
    'url: {url}.\n'
    'HEADERS: {headers}.\n'
    'params: {params}.\n'
    'error: {error}'
)
STATUS_NOT_OK_ERROR = (
    'Код ответа от API-сервиса Практикум Домашка не 200.\n'
    'Код ответа: {status_code}.\n'
    'url: {url}.\n'
    'HEADERS: {headers}.\n'
    'params: {params}.\n'
)
ERROR_KEYS_IN_RESPONSE = ('code', 'error')
RESPONSE_HAS_ERROR_KEY_ERROR = (
    'Ответ API содержит ошибку.\n'
    'url: {url}.\n'
    'HEADERS: {headers}.\n'
    'params: {params}.\n'
    'ключ: {key}.\n'
    'error: {error}'
)
RESPONSE_IS_NOT_DICT_ERROR = (
    'Ответ API не является словарем.\n'
    'Полученный типа данных: {data_type}.'
)
KEY_IS_NOT_IN_RESPONSE_ERROR = (
    'Отсутствует обязательный элемент в ответе API: homeworks.'
)
HOMEWORKS_IS_NOT_LIST_ERROR = (
    'Ключ homeworks не содержит список.\n'
    'Полученный типа данных: {data_type}.'
)


def check_tokens() -> None:
    """Проверяет доступность переменных окружения."""
    missing_tokens = ', '.join(
        token for token in TOKENS if not globals()[token]
    )
    if missing_tokens:
        logging.critical(NOT_TOKENS_ERROR.format(tokens=missing_tokens))
        raise ValueError(NOT_TOKENS_ERROR.format(tokens=missing_tokens))


def send_message(bot: TeleBot, message: str) -> None:
    """Отправляет сообщение в Telegram-чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(SEND_MESSAGE_SUCCESS.format(message=message))
    except Exception:
        logging.exception(SEND_MESSAGE_ERROR.format(message=message))


def get_api_answer(timestamp: int) -> dict:
    """Делает запрос к эндпоинту API-сервиса Практикум Домашка."""
    request_parameters = dict(
        url=ENDPOINT,
        headers=HEADERS,
        params={'from_date': timestamp}
    )
    try:
        response = requests.get(**request_parameters)
    except requests.RequestException as error:
        raise ConnectionError(REQUEST_ERROR.format(
            error=error,
            **request_parameters
        ))
    if response.status_code != HTTPStatus.OK:
        raise StatusCodeIsNot200Error(STATUS_NOT_OK_ERROR.format(
            status_code=response.status_code,
            **request_parameters
        ))
    response = response.json()
    for key in ERROR_KEYS_IN_RESPONSE:
        if key in response:
            raise ValueError(RESPONSE_HAS_ERROR_KEY_ERROR.format(
                key=key,
                error=response.get(key),
                **request_parameters
            ))
    return response


def check_response(response: dict) -> None:
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError(RESPONSE_IS_NOT_DICT_ERROR.format(
            data_type=type(response)
        ))
    if 'homeworks' not in response:
        raise KeyError(KEY_IS_NOT_IN_RESPONSE_ERROR)
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(HOMEWORKS_IS_NOT_LIST_ERROR.format(
            data_type=type(homeworks)
        ))


def parse_status(homework: dict) -> str:
    """Извлекает статус домашней работы."""
    logging.debug('Начало извлечения статуса домашней работы.')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    homework_keys = {
        'homework_name': homework_name,
        'status': homework_status
    }
    for key, value in homework_keys.items():
        if value is None:
            error_message = (
                f'В словаре homework отсутствует обязательный ключ: {key}.'
            )
            logging.error(error_message)
            raise KeyError(error_message)
    if homework_status not in HOMEWORK_VERDICTS:
        error_message = (
            f'Неизвестное значение статуса домашней работы: {homework_status}'
        )
        logging.error(error_message)
        raise ValueError(error_message)
    return (
        f'Изменился статус проверки работы "{homework_name}". '
        f'{HOMEWORK_VERDICTS.get(homework_status)}'
    )


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_status = ''
    last_error = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homeworks = response.get('homeworks')
            if not homeworks:
                logging.debug('Статус домашней работы не изменился.')
                continue
            message = parse_status(homeworks[0])
            if message != last_status:
                logging.debug('Статус домашней работы изменился.')
                send_message(bot, message)
                last_status = message
            else:
                logging.debug('Статус домашней работы не изменился.')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if message != last_error:
                send_message(bot, message)
                last_error = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            '%(asctime)s %(levelname)s: %(funcName)s, '
            'строка № %(lineno)d - %(message)s'
        ),
        handlers=[
            logging.StreamHandler(stream=sys.stdout),
            logging.FileHandler(
                filename=__file__ + '.log',
                mode='w',
                encoding='utf-8'
            )
        ]
    )
    main()
