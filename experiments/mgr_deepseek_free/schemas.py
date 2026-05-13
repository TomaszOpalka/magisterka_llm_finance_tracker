"""
Pydantic v2 schemas for the Finance Track system.
Defines models for asset creation, read, and analytics responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FinancialAssetBase(BaseModel):
    """
    Base schema containing common fields for a financial asset.
    Used as a parent for creation and read schemas.
    """

    ticker_symbol: str = Field(
        ...,
        pattern=r"^[A-Z]{1,5}$",
        description="Stock ticker symbol, 1-5 uppercase letters (e.g. AAPL)",
    )
    last_price: float = Field(..., ge=0, description="Latest observed price (>=0)")
    market_cap: int = Field(..., description="Market capitalisation as an integer")
    last_updated: datetime | None = Field(
        default=None, description="Timestamp of the last price update"
    )


class FinancialAssetCreate(FinancialAssetBase):
    """
    Schema used when creating a new asset.
    Does not include the asset_id because it is generated server-side.
    """
    pass


class FinancialAsset(FinancialAssetBase):
    """
    Schema returned when reading a single asset.
    Includes the primary key asset_id and supports ORM mapping.
    """

    asset_id: str = Field(..., description="Primary key (UUID)")

    model_config = ConfigDict(from_attributes=True)


class AssetAnalytics(BaseModel):
    """
    Legacy analytics model – contains only the 30-day moving average.
    Retained for backward compatibility.
    """

    ticker_symbol: str
    moving_average_30d: float


class AnalyticsResponse(AssetAnalytics):
    """
    Full analytics response for the /assets/{ticker}/analytics endpoint.
    Extends AssetAnalytics with the 14-day RSI.
    """

    rsi_14: float = Field(..., description="14-day Relative Strength Index (0-100)")