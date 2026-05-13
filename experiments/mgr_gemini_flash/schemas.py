from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class FinancialAssetBase(BaseModel):
    """Base schema for common asset attributes."""
    ticker_symbol: str
    last_price: float
    market_cap: Optional[float] = None

class FinancialAssetCreate(FinancialAssetBase):
    """Schema for creating a new asset."""
    pass

class FinancialAsset(FinancialAssetBase):
    """Schema for returning asset data, including system-generated fields."""
    asset_id: str
    last_updated: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class AssetAnalytics(BaseModel):
    """Sub-model for specific technical indicators."""
    moving_average_30d: Optional[float] = None
    rsi_14: Optional[float] = None

class AnalyticsResponse(BaseModel):
    """Comprehensive response for the analytics endpoint."""
    ticker_symbol: str
    moving_average_30d: Optional[float] = None
    rsi_14: Optional[float] = None
    data_points: int