from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    """Abstract architectural blueprint for database tables."""
    pass

class FinancialAsset(Base):
    """
    Database entity configuration for financial trackers.
    Renamed internal asset tracking coordinate from last_price to current_market_price.
    Database field integrity constraints require asset_id as string PK.
    """
    __tablename__ = "financial_assets"

    asset_id = Column(String, primary_key=True, nullable=False)
    ticker_symbol = Column(String, unique=True, index=True, nullable=False)
    current_market_price = Column(Float, default=0.0, nullable=False)
    market_cap = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)