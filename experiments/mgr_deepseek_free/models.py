"""
SQLAlchemy 2.0 ORM models for the Finance Track system.
Table columns are strictly snake_case. The primary key is asset_id (String).
"""

from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Float, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base class for all models."""
    pass


class FinancialAsset(Base):
    """
    Representation of a financial asset.
    Table name: financial_assets
    Primary key: asset_id (UUID string) – never 'id'.
    """

    __tablename__ = "financial_assets"

    asset_id: Mapped[str] = mapped_column(String, primary_key=True)

    ticker_symbol: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )

    last_price: Mapped[float] = mapped_column(Float, nullable=True)

    market_cap: Mapped[int] = mapped_column(BigInteger, nullable=True)

    last_updated: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<FinancialAsset(ticker='{self.ticker_symbol}', "
            f"price={self.last_price}, asset_id='{self.asset_id}')>"
        )