"""
Pydantic v2 schemas for the Finance Track system.
All API-visible fields use camelCase via an automatic alias generator.
Internal database columns remain snake_case and are mapped transparently.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


def _to_camel(snake: str) -> str:
    """Convert snake_case string to camelCase (e.g., asset_id -> assetId)."""
    parts = snake.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelCaseModel(BaseModel):
    """
    Base model that configures automatic camelCase aliasing.
    Fields defined in snake_case are serialised as camelCase,
    and camelCase input is accepted and mapped back to snake_case.
    """
    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
    )


class FinancialAssetBase(CamelCaseModel):
    """
    Common fields for financial assets.
    API keys: tickerSymbol, lastPrice, marketCap, lastUpdated.
    Database columns remain: ticker_symbol, last_price, market_cap, last_updated.
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
    Schema used for creating a new asset.
    Inherits all fields and aliases; assetId is not included.
    """
    pass


class FinancialAsset(FinancialAssetBase):
    """
    Schema for reading an asset.
    Adds the primary key asset_id, exposed as 'assetId'.
    Supports ORM mapping (from_attributes=True).
    """
    asset_id: str = Field(..., description="Primary key (UUID)")

    # Override config to add ORM support while keeping camelCase aliasing
    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class AssetAnalytics(CamelCaseModel):
    """
    Legacy analytics response, containing only the 30-day moving average.
    Keys: tickerSymbol, movingAverage30d.
    """
    ticker_symbol: str
    moving_average_30d: float


class AnalyticsResponse(AssetAnalytics):
    """
    Full analytics response for the /assets/{ticker}/analytics endpoint.
    Extends AssetAnalytics with the 14-day RSI.
    Keys: tickerSymbol, movingAverage30d, rsi14.
    """
    rsi_14: float = Field(..., description="14-day Relative Strength Index (0-100)")