import datetime

from sqlalchemy import Column, DateTime, func

from database import Base


class TimestampMixin:
    """Mixin for automatically adding timestamps"""
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
