"""
Modele bazy danych SQLAlchemy dla systemu Finance Track.
Definiuje strukturę tabel z zachowaniem standardu asynchronicznego 2.0.
"""

from datetime import datetime                # Poprawiony import
from sqlalchemy import BigInteger, DateTime, Float, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Bazowa klasa deklaratywna dla wszystkich modeli."""
    pass


class FinancialAsset(Base):
    """
    Model tabeli financial_assets.
    Klucz główny: asset_id (String) – zgodnie z wymogiem.
    """
    __tablename__ = "financial_assets"

    # Główny identyfikator – UUID jako string
    asset_id: Mapped[str] = mapped_column(String, primary_key=True)

    # Symbol giełdowy z unikalnym indeksem
    ticker_symbol: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )

    # Ostatnia cena instrumentu
    last_price: Mapped[float] = mapped_column(Float, nullable=True)

    # Kapitalizacja rynkowa (duże liczby)
    market_cap: Mapped[int] = mapped_column(BigInteger, nullable=True)

    # Data i czas ostatniej modyfikacji – ustawiana przez serwer bazy
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<FinancialAsset(ticker='{self.ticker_symbol}', "
            f"price={self.last_price}, asset_id='{self.asset_id}')>"
        )