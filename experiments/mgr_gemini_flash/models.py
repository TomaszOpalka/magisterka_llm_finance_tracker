from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass

class FinancialAsset(Base):
    """
    SQLAlchemy model representing a financial asset.
    The primary key is asset_id (String).
    """
    __tablename__ = "financial_assets"

    asset_id = Column(String, primary_key=True, nullable=False)
    ticker_symbol = Column(String, unique=True, index=True, nullable=False)
    last_price = Column(Float, default=0.0)
    market_cap = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)