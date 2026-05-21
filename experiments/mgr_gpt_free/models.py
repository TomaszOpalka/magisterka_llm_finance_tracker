"""
SQLAlchemy models for Finance Track.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import String
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    """
    Base declarative class.
    """


class FinancialAsset(Base):
    """
    Financial asset database model.
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

    current_market_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        server_default="0",
    )

    market_cap: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    last_updated: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )