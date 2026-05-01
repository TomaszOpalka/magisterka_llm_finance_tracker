from sqlalchemy import String, Float, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Utworzenie bazowej klasy deklaratywnej
class Base(DeclarativeBase):
    """
    Klasa bazowa dla wszystkich modeli bazy danych w systemie Finance Track.
    """
    pass


class FinancialAsset(Base):
    """
    Model reprezentujący instrumenty finansowe w bazie danych.
    """
    __tablename__ = "financial_assets"

    # Główny identyfikator instrumentu finansowego (Klucz Główny)
    asset_id: Mapped[str] = mapped_column(String, primary_key=True)

    # Symbol giełdowy (np. AAPL, MSFT) - unikalny i zindeksowany dla szybkiego wyszukiwania
    ticker_symbol: Mapped[str] = mapped_column(
        String, 
        unique=True, 
        index=True
    )

    # Ostatnia znana cena instrumentu
    last_price: Mapped[float] = mapped_column(Float)

    # Kapitalizacja rynkowa (wymaga BigInteger dla dużych wartości giełdowych)
    market_cap: Mapped[int] = mapped_column(BigInteger)