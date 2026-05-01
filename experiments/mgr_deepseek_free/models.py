"""
Definicje modeli bazy danych (ORM) w architekturze modularnej.
Wykorzystuje deklaratywną bazę SQLAlchemy 2.0.
"""

from sqlalchemy import BigInteger, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Klasa bazowa dla wszystkich modeli (zastępuje declarative_base() z 1.x)
class Base(DeclarativeBase):
    """Bazowa klasa deklaratywna, od której dziedziczą wszystkie modele."""
    pass


class FinancialAsset(Base):
    """
    Model reprezentujący aktywa finansowe (np. akcje, ETF-y).
    Nazwa tabeli w bazie danych: financial_assets.
    """
    __tablename__ = "financial_assets"

    # Główny identyfikator – celowo nie nazwany 'id' (wymóg: asset_id)
    asset_id: Mapped[str] = mapped_column(String, primary_key=True)

    # Symbol giełdowy, np. 'AAPL', 'GOOGL'
    # Unikalny i indeksowany dla szybkiego wyszukiwania
    ticker_symbol: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )

    # Ostatnia znana cena instrumentu
    last_price: Mapped[float] = mapped_column(Float, nullable=True)

    # Kapitalizacja rynkowa (duże liczby całkowite)
    market_cap: Mapped[int] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        """Czytelna reprezentacja obiektu w logach i debugerze."""
        return f"<FinancialAsset(ticker='{self.ticker_symbol}', price={self.last_price})>"