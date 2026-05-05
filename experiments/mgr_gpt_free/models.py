"""
Definicje modeli ORM dla systemu Finance Track.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """
    Klasa bazowa dla modeli ORM.
    """
    pass


class FinancialAsset(Base):
    """
    Model reprezentujący aktywo finansowe.
    """

    __tablename__ = "financial_assets"

    # Klucz główny – zgodnie z kontraktem: asset_id (NIE zmieniamy!)
    asset_id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
    )

    ticker_symbol: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    last_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    market_cap: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    # Data ostatniej aktualizacji (domyślnie ustawiana przez bazę)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=True,
    )