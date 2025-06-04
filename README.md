# URL Alias Service

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
[![Coverage Status](https://coveralls.io/repos/github/Neizvestnyj/url-alias-service/badge.svg?branch=master)](https://coveralls.io/github/Neizvestnyj/url-alias-service?branch=master)

Сервис для преобразования длинных URL в короткие уникальные ссылки с REST API интерфейсом.

## Оглавление

- [Функциональность](#функциональность)
- [Требования](#требования)
- [Быстрый старт](#быстрый-старт)
  - [Запуск с Docker](#запуск-с-docker-рекомендуется)
  - [Локальная установка](#локальная-установка)
- [API Документация](#api-документация)
- [Эндпоинты](#эндпоинты)
- [Тестирование](#тестирование)
- [Разработка](#разработка)
- [Структура проекта](#структура-проекта)

## Функциональность

✅ **Основные возможности:**
- Создание коротких ссылок с настраиваемым сроком действия (по умолчанию 1 день)
- Перенаправление на оригинальные URL
- Деактивация ссылок без физического удаления
- Аутентификация пользователей (Basic Auth)

📊 **Дополнительные возможности:**
- Сбор статистики по переходам
- Постраничное отображение ссылок
- Фильтрация по активным ссылкам
- Swagger документация

## Требования

- Python 3.11+
- PostgreSQL 17+
- Docker (опционально)

## Быстрый старт

### Запуск с Docker (рекомендуется)

```bash
# Сборка и запуск контейнеров
make build
make up

# Применение миграций
make migrate
```

Сервис будет доступен по адресу: `http://localhost:8000`

### Локальная установка

1. Установите зависимости:
    ```bash
    poetry install --with test,dev
    ```
2. Запустите сервис:
    ```bash
    poetry run uvicorn app.main:app --reload
    ```

## API Документация

После запуска сервиса документация доступна по адресу:
- Swagger UI: `http://localhost:8000/docs`

## Эндпоинты

### Публичные

- `GET /r/{short_key}` - Перенаправление на оригинальный URL
  - Возвращает 307 редирект или 404 если ссылка недействительна

### Приватные (требуют аутентификации)

- `POST /api/v1/auth/register` - Регистрация пользователя
- `GET /api/v1/urls` - Список созданных ссылок
- `POST /api/v1/urls` - Создание новой короткой ссылки
- `DELETE /api/v1/urls/{url_id}` - Деактивация ссылки

## Тестирование

Проект включает юнит и интеграционные тесты:

```bash
# Запуск тестов
make test

# Покрытие кода
start htmlcov/index.html # open для Linux
```

Тесты запускаются автоматически в CI при пуше в репозиторий.

## Разработка

### Форматирование кода
Проект использует [Ruff](https://beta.ruff.rs/) для линтинга и форматирования:

```bash
# Только проверка стиля
make lint 

# Форматирование кода и исправление ошибок
make format
```

### Миграции

```bash
# Создание новой миграции
poetry run alembic revision --autogenerate -m "description"

# Применение миграций
make migrate
```
