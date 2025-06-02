from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.db.models.base import Base


class User(Base):
    """Модель для хранения пользователей (для Basic Auth)."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False,
    )
