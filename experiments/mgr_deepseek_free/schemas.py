"""
Pydantic v2 schemas for the Finance Track system.
All public API keys are camelCase. Incoming JSON with camelCase keys is
automatically mapped to internal snake_case attributes via an alias generator.
Database columns remain snake_case (asset_id, ticker_symbol, etc.).
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


def _to_camel(snake: str) -> str:
    """Convert a snake_case string to camelCase (e.g., asset_id -> assetId)."""
    parts = snake.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelCaseModel(BaseModel):
    """
    Base class that instructs Pydantic to:
    - Serialize all fields to camelCase using `_to_camel`.
    - Accept both camelCase and snake_case during deserialization
      (populate_by_name=True allows access by the original field name).
    """
    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
    )


class FinancialAssetBase(CamelCaseModel):
    """
    Common fields for a financial asset.
    API keys (camelCase): tickerSymbol, lastPrice, marketCap, lastUpdated.
    Internal Python attributes are snake_case (ticker_symbol, etc.).
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
    Payload for creating a new asset.
    Accepts camelCase keys (e.g., tickerSymbol, lastPrice) and
    populates the snake_case attributes internally.
    """
    pass


class FinancialAsset(FinancialAssetBase):
    """
    Schema for reading an asset.
    Adds the primary key field: asset_id (API key: assetId).
    Supports ORM mapping (from_attributes=True).
    """
    asset_id: str = Field(..., description="Primary key (UUID)")

    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class AssetAnalytics(CamelCaseModel):
    """
    Legacy analytics response – contains only the 30-day moving average.
    API keys: tickerSymbol, movingAverage30d.
    """
    ticker_symbol: str
    moving_average_30d: float


class AnalyticsResponse(AssetAnalytics):
    """
    Full analytics response for the /assets/{ticker}/analytics endpoint.
    API keys: tickerSymbol, movingAverage30d, rsi14.
    """
    rsi_14: float = Field(..., description="14-day Relative Strength Index (0-100)")