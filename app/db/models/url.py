from datetime import datetime, timedelta

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.db.models.base import Base


class URL(Base):
    """Модель для хранения коротких URL."""

    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, nullable=False, index=True)
    short_key = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: func.now() + timedelta(days=1),
        server_default=func.now() + timedelta(days=1),
    )
    created_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False,
    )
    click_count = Column(Integer, default=0, nullable=False)
