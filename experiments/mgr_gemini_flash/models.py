from sqlalchemy import String, Float, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """Klasa bazowa dla wszystkich modeli w systemie."""
    pass

class FinancialAsset(Base):
    """Reprezentacja tabeli aktywów finansowych."""
    __tablename__ = "financial_assets"

    # Klucz główny o nazwie asset_id zgodnie z wymaganiami
    asset_id: Mapped[str] = mapped_column(
        String, 
        primary_key=True, 
        nullable=False
    )

    # Symbol giełdowy (np. AAPL, BTC) - unikalny i indeksowany
    ticker_symbol: Mapped[str] = mapped_column(
        String, 
        unique=True, 
        index=True, 
        nullable=False
    )

    # Ostatnia odnotowana cena
    last_price: Mapped[float] = mapped_column(
        Float, 
        nullable=True
    )

    # Kapitalizacja rynkowa (użycie BigInteger dla dużych wartości)
    market_cap: Mapped[int] = mapped_column(
        BigInteger, 
        nullable=True
    )

    def __repr__(self) -> str:
        return f"<FinancialAsset(ticker={self.ticker_symbol}, price={self.last_price})>"