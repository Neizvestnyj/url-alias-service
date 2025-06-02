from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.core.config import settings
from app.db.models import Base

# Настройка логирования из alembic.ini
config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)
fileConfig(config.config_file_name)

# Метаданные моделей для миграций
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Выполняет миграции в оффлайн-режиме (без подключения к базе данных).

    :returns: None
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Выполняет миграции в онлайн-режиме (с подключением к базе данных).

    :returns: None
    """
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=None,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
