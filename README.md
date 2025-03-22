# Бот-ассистент

Telegram бот для проверки статуса домашней работы. 

## Функции проекта

* Опрашивает API сервиса Практикум Домашка и проверяет статус отправленной 
на ревью работы: работа принята на проверку; работа возвращена для исправления 
ошибок; работа принята. Анализирует статус работы и отправляет сообщение если 
статус изменился.
* Отправляет сообщения в Telegram при возникновении важных проблем в работе 
программы.
* Настроено логирование


## Стек технологий
* [Python](https://www.python.org/)
* [pyTelegramBotAPI](https://pytba.readthedocs.io/en/latest/)

## Как развернуть проект
1. Клонируйте репозиторий и перейдите в директорию homework_bot
```bash
git clone git@github.com:igorKolomitseff/homework_bot.git
cd homework_bot
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python3 -m venv venv
source venv/bin/activate  # Для Linux и macOS
source venv/Scripts/activate  # Для Windows
```

3. Обновите pip и установите зависимости проекта:
```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

4. Создайте .env файл в корневой директории и заполните его данными в 
соответствии с файлом .env.example

5. Запустите проект:
```bash
python3 homework.py
```

### Автор

[Игорь Коломыцев](https://github.com/igorKolomitseff)
