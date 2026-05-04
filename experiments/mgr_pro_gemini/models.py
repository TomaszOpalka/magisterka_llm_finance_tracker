from datetime import datetime
from sqlalchemy import String, Float, BigInteger, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Klasa bazowa dla wszystkich modeli w systemie."""
    pass


class FinancialAsset(Base):
    """Model reprezentujący instrumenty finansowe w bazie danych SQLite."""
    __tablename__ = "financial_assets"

    # Główny identyfikator (nieużywanie nazwy 'id' zgodnie z wytycznymi)
    asset_id: Mapped[str] = mapped_column(String, primary_key=True)

    ticker_symbol: Mapped[str] = mapped_column(
        String, 
        unique=True, 
        index=True
    )

    last_price: Mapped[float] = mapped_column(Float)

    market_cap: Mapped[int] = mapped_column(BigInteger)

    # Nowa kolumna: Data ostatniej aktualizacji (z mechanizmem server_default)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        nullable=True
    )