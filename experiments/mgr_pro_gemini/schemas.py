from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class FinancialAssetBase(BaseModel):
    """Base schema containing common financial asset attributes."""
    ticker_symbol: str = Field(..., description="The unique stock ticker symbol")
    last_price: Optional[float] = Field(None, ge=0.0, description="Latest traded price")
    market_cap: Optional[float] = Field(None, ge=0.0, description="Total market capitalization")

class FinancialAssetCreate(FinancialAssetBase):
    """Schema used for creating a new financial asset."""
    pass

class FinancialAsset(FinancialAssetBase):
    """
    Complete Financial Asset schema representing database records.
    Configured for ORM mode to seamlessly translate SQLAlchemy models.
    """
    asset_id: str = Field(..., description="Primary key identifier")
    last_updated: Optional[datetime] = Field(None, description="Timestamp of last data sync")

    model_config = ConfigDict(from_attributes=True)

class AssetAnalytics(BaseModel):
    """Base schema for calculated technical indicators."""
    moving_average_30d: Optional[float] = Field(None, description="30-day Simple Moving Average")
    rsi_14: Optional[float] = Field(None, description="14-period Relative Strength Index")

class AnalyticsResponse(AssetAnalytics):
    """
    Response schema for the analytics endpoint.
    Inherits technical indicators from AssetAnalytics and adds the ticker symbol.
    """
    ticker_symbol: str = Field(..., description="The specific stock ticker symbol")