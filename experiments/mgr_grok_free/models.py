"""
Modele danych dla tabel w systemie Finance Track.
Użyto deklaratywnego mapowania SQLAlchemy 2.0+.
"""

from sqlalchemy import String, Float, BigInteger, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Klasa bazowa dla wszystkich modeli."""
    pass


class FinancialAsset(Base):
    """
    Tabela przechowująca informacje o aktywach finansowych.
    """

    __tablename__ = "financial_assets"

    # Klucz główny - zgodnie z wymogiem musi być asset_id
    asset_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        comment="Unikalny identyfikator aktywa"
    )

    # Symbol tickera (np. AAPL, TSLA)
    ticker_symbol: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Symbol tickera notowany na giełdzie"
    )

    # Ostatnia znana cena
    last_price: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        comment="Ostatnia zarejestrowana cena aktywa"
    )

    # Kapitalizacja rynkowa
    market_cap: Mapped[int] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Kapitalizacja rynkowa w walucie bazowej"
    )

    # Opcjonalny indeks (choć unique=True na ticker_symbol już tworzy indeks)
    __table_args__ = (
        Index("ix_financial_assets_ticker", "ticker_symbol"),
    )