import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """Base class for SQLAlchemy 2.0 declarative models."""
    pass

class FinancialAsset(Base):
    """
    Database model representing a financial asset.
    Strictly uses 'asset_id' as the Primary Key to satisfy architecture constraints.
    """
    __tablename__ = "financial_assets"

    asset_id: Mapped[str] = mapped_column(
        String, 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    ticker_symbol: Mapped[str] = mapped_column(
        String, 
        unique=True, 
        index=True, 
        nullable=False
    )
    last_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )