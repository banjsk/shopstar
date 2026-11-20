# starheartshop ⭐

Демонстрационный Telegram-магазин на Python.

## Возможности
- Каталог демонстрационных пакетов
- Карточки товаров
- Создание тестовых заказов
- История заказов пользователя
- Команда администратора со сводкой
- SQLite для хранения тестовых заказов

> Важно: проект работает только в DEMO-режиме. Он не принимает реальные платежи и не продаёт/не отправляет Telegram Stars.

## Локальный запуск
1. Создай бота через [@BotFather](https://t.me/BotFather).
2. Установи Python 3.10 или новее.
3. Установи зависимости: `pip install -r requirements.txt`.
4. Задай переменные окружения:
   - `BOT_TOKEN` — токен бота из BotFather.
   - `ADMIN_ID` — твой числовой Telegram ID (узнать командой `/id`; необязательно).
   - `SUPPORT_USERNAME` — username поддержки без символа @ (необязательно).
   - `DB_PATH` — путь к файлу базы (по умолчанию `starheartshop.db`).
5. Запусти: `python bot.py`.

## Деплой на Render
Создай Background Worker из этого GitHub-репозитория:
- Build Command: `pip install -r requirements.txt`
- Start Command: `python bot.py`

В Environment добавь `BOT_TOKEN`, а также необязательные `ADMIN_ID` и `SUPPORT_USERNAME`.
Для сохранения заказов между перезапусками подключи persistent disk и задай `DB_PATH` внутри точки монтирования.

## Безопасность
- Не добавляй токен бота в исходники, README или GitHub.
- Храни токен только в Environment Variables на хостинге.
- Если токен случайно попал в публичный репозиторий, отзови его через BotFather.
