from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import Optional
from datetime import datetime

class FinancialAssetBase(BaseModel):
    """
    Base schema defining the core attributes of a financial asset.
    Uses Pydantic's ConfigDict and AliasGenerator to automatically map 
    internal snake_case fields to external camelCase JSON keys.
    """
    ticker_symbol: str = Field(..., description="The unique stock ticker symbol")
    last_price: Optional[float] = Field(None, ge=0.0, description="Latest traded price")
    market_cap: Optional[float] = Field(None, ge=0.0, description="Total market capitalization")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

class FinancialAssetCreate(FinancialAssetBase):
    """Schema used for accepting incoming creation payloads."""
    pass

class FinancialAsset(FinancialAssetBase):
    """
    Complete response schema including system-generated fields.
    Automatically serializes asset_id to assetId and last_updated to lastUpdated.
    """
    asset_id: str = Field(..., description="Primary key identifier")
    last_updated: Optional[datetime] = Field(None, description="Timestamp of last data sync")

class AssetAnalytics(BaseModel):
    """Base schema for technical indicators."""
    moving_average_30d: Optional[float] = Field(None, description="30-day Simple Moving Average")
    rsi_14: Optional[float] = Field(None, description="14-period Relative Strength Index")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

class AnalyticsResponse(AssetAnalytics):
    """Response schema combining technical indicators with the asset identifier."""
    ticker_symbol: str = Field(..., description="The specific stock ticker symbol")