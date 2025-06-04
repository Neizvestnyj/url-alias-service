# Makefile для управления проектом url-alias-service
#
# Команды:
#   make build         Собрать Docker-образы
#   make up            Запустить контейнеры в фоновом режиме
#   make down          Остановить и удалить контейнеры
#   make logs          Показать логи контейнеров
#   make test          Запустить тесты
#   make test_docker   Запустить тесты в docker
#   make lint          Запустить линтер (ruff)
#   make format        Форматировать код (ruff)
#   make migrate       Выполнить миграции базы данных
# Переменные окружения:
#   APP_NAME: Окружение (default: dev)

APP_NAME := url-alias-service
COMPOSE := docker compose

.PHONY: all build up down logs test lint format migrate

# Сборка Docker-образов
build:
	@echo "Building Docker images..."
	$(COMPOSE) -f docker-compose.yml build

# Запуск контейнеров
up:
	@echo "Starting containers..."
	$(COMPOSE) -f docker-compose.yml up -d

# Остановка и удаление контейнеров
down:
	@echo "Stopping and removing containers..."
	$(COMPOSE) -f docker-compose.yml down

# Показ логов
logs:
	@echo "Showing container logs..."
	$(COMPOSE) -f docker-compose.yml logs -f

# Запуск тестов
test:
	@echo "Running tests..."poetry run coverage run -m pytest
	poetry run pytest tests -v --cov=app --cov-report=html

# Запуск тестов
test_docker:
	@echo "Running docker tests..."
	$(COMPOSE) -f docker-compose.yml run --rm app pytest tests -v --cov=app --cov-report=html

# Запуск линтера
lint:
	@echo "Running linter..."
	poetry run ruff check app tests

# Форматирование кода
format:
	@echo "Formatting code..."
	poetry run ruff format app tests

# Выполнение миграций базы данных
migrate:
	@echo "Running database migrations..."
	poetry run alembic upgrade head
