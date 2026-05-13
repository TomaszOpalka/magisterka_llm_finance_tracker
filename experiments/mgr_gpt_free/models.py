"""
SQLAlchemy models for Finance Track (database layer).
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import BigInteger, DateTime, Float, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base SQLAlchemy class.
    """
    pass


class FinancialAsset(Base):
    """
    Database model (snake_case enforced).
    """

    __tablename__ = "financial_assets"

    asset_id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    ticker_symbol: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    last_price: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    market_cap: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
    )

    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )