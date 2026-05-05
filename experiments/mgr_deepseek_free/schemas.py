"""
Schemas (Pydantic v2) for the Finance Track system.
Includes strict validation and support for ORM models.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class FinancialAssetBase(BaseModel):
    """Base schema with common fields for asset creation and reading."""

    ticker_symbol: str = Field(
        ...,
        pattern=r"^[A-Z]{1,5}$",
        description="Stock ticker symbol (1-5 uppercase letters), e.g., AAPL",
    )
    last_price: float = Field(..., ge=0, description="Last observed price (>=0)")
    market_cap: int = Field(..., description="Market capitalization (raw value)")
    last_updated: datetime | None = Field(
        default=None,
        description="Timestamp of the last data update",
    )


class FinancialAssetCreate(FinancialAssetBase):
    """Schema for creating a new asset."""
    pass


class FinancialAsset(FinancialAssetBase):
    """Schema for reading an asset, including its primary key."""
    asset_id: str = Field(..., description="Primary key (UUID)")

    model_config = ConfigDict(from_attributes=True)


class AssetAnalytics(BaseModel):
    """Response schema for the analytics endpoint."""
    ticker_symbol: str = Field(..., description="Stock ticker symbol")
    moving_average_30d: float = Field(
        ..., description="30-day simple moving average of the closing price"
    )