import logging
from logging.handlers import RotatingFileHandler


def setup_logging(environment: str = "development") -> logging.Logger:
    """
    Настраивает логирование приложения.

    :param environment: Окружение приложения (development, production).
    :type environment: str
    :returns: Настроенный логгер.
    :rtype: logging.Logger
    """
    logger = logging.getLogger("url_alias_service")

    # Предотвращаем дублирование обработчиков
    if logger.handlers:
        return logger

    # Уровень логирования в зависимости от окружения
    log_level = logging.DEBUG if environment == "development" else logging.INFO

    # Формат логов
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(log_level)

    # Файловый обработчик с ротацией
    file_handler = RotatingFileHandler(
        "url_alias_service.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(log_level)

    # Настройка логгера
    logger.setLevel(log_level)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def update_logging(environment: str) -> None:
    """
    Обновляет уровень логирования в зависимости от окружения.

    :param environment: Окружение приложения (development, production).
    :type environment: str
    :returns: None
    """
    logger = logging.getLogger("url_alias_service")
    log_level = logging.DEBUG if environment == "development" else logging.INFO
    logger.setLevel(log_level)
    for handler in logger.handlers:
        handler.setLevel(log_level)


logger = setup_logging()
