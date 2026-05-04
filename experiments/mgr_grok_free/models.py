"""
Modele danych dla tabel w systemie Finance Track.
Użyto deklaratywnego mapowania SQLAlchemy 2.0+.
"""

from sqlalchemy import String, Float, BigInteger, Index, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime


class Base(DeclarativeBase):
    """Klasa bazowa dla wszystkich modeli."""
    pass


class FinancialAsset(Base):
    """
    Tabela przechowująca informacje o aktywach finansowych.
    Klucz główny: asset_id (zgodnie z kontraktem projektu).
    """

    __tablename__ = "financial_assets"

    # KLUCZ GŁÓWNY
    asset_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        comment="Unikalny identyfikator aktywa"
    )

    ticker_symbol: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Symbol tickera notowany na giełdzie"
    )

    last_price: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        comment="Ostatnia zarejestrowana cena aktywa"
    )

    market_cap: Mapped[int] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Kapitalizacja rynkowa w walucie bazowej"
    )

    last_updated: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=True,
        comment="Data i godzina ostatniej aktualizacji danych rynkowych"
    )

    # Indeksy
    __table_args__ = (
        Index("ix_financial_assets_ticker", "ticker_symbol"),
    )