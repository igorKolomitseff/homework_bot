from http import HTTPStatus
import logging
import os
import sys
import time

import requests
from dotenv import load_dotenv
from telebot import TeleBot

from exceptions import (
    StatusCodeIsNot200Error, UnavailableAPIError
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
    try:
        logging.debug(
            'Выполняется запрос к эндпоинту API-сервиса Практикум Домашка.'
        )
        response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp},
        )
        if response.status_code != HTTPStatus.OK:
            error_message = (
                'Ошибка запроса к API-сервису Практикум Домашка. '
                f'Код ответа API: {response.status_code}'
            )
            logging.error(error_message)
            raise StatusCodeIsNot200Error(error_message)
        logging.debug(
            'Запрос к эндпоинту API-сервиса Практикум Домашка выполнен.'
        )
        return response.json()
    except requests.RequestException as error:
        error_message = (
            'Эндпоит сервиса Практикум Домашка недоступен. '
            f'Код ответа API: {response.status_code}. {error}'
        )
        logging.error(error_message)
        raise UnavailableAPIError(error_message)


def check_response(response: dict) -> None:
    """Проверяет ответ API на соответствие документации."""
    logging.debug('Начало проверки ответа API на соответствие документации.')
    if not isinstance(response, dict):
        error_message = (
            'Ответ API не является словарем.'
        )
        logging.error(error_message)
        raise TypeError(error_message)
    for key in ('current_date', 'homeworks'):
        if key not in response:
            error_message = (
                f'Отсутствует обязательный элемент в ответе API: {key}.'
            )
            logging.error(error_message)
            raise KeyError(error_message)
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        error_message = ('Ответ API с ключом homeworks не содержит список.')
        logging.error(error_message)
        raise TypeError(error_message)
    logging.debug('Весь ответ API соответствует документации.')


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
    try:
        check_tokens()
    except ValueError:
        sys.exit()
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
