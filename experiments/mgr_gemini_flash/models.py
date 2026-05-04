from sqlalchemy import String, Float, BigInteger, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class FinancialAsset(Base):
    __tablename__ = "financial_assets"

    # Klucz główny - rygorystycznie asset_id
    asset_id: Mapped[str] = mapped_column(String, primary_key=True)
    
    ticker_symbol: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    
    last_price: Mapped[float] = mapped_column(Float, nullable=False)
    
    market_cap: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    # Nowa kolumna z automatycznym czasem po stronie serwera
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<FinancialAsset(asset_id={self.asset_id}, ticker={self.ticker_symbol})>"