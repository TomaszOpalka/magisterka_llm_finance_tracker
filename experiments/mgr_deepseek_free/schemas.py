"""
Pydantic v2 schemas for the Finance Track system.
Internal attribute names follow the database columns (e.g., current_market_price),
while the public API uses camelCase aliases. The field previously named last_price
is now current_market_price, but its JSON key remains 'lastPrice'.
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
    Base model with automatic camelCase alias generation.
    Fields may override the alias explicitly when needed.
    """
    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
    )


class FinancialAssetBase(CamelCaseModel):
    """
    Common fields for a financial asset.
    - ticker_symbol -> tickerSymbol (automatic)
    - current_market_price -> lastPrice (explicit alias)
    - market_cap -> marketCap (automatic)
    - last_updated -> lastUpdated (automatic)
    """
    ticker_symbol: str = Field(
        ...,
        pattern=r"^[A-Z]{1,5}$",
        description="Stock ticker symbol, 1-5 uppercase letters (e.g. AAPL)",
    )
    current_market_price: float = Field(
        ...,
        ge=0,
        alias="lastPrice",
        description="Latest observed market price (>=0). Serialised as 'lastPrice'.",
    )
    market_cap: int = Field(..., description="Market capitalisation as an integer")
    last_updated: datetime | None = Field(
        default=None, description="Timestamp of the last price update"
    )


class FinancialAssetCreate(FinancialAssetBase):
    """
    Payload for creating a new asset.
    Accepts camelCase keys: tickerSymbol, lastPrice, marketCap, lastUpdated.
    """
    pass


class FinancialAsset(FinancialAssetBase):
    """
    Schema for reading an asset.
    Adds primary key asset_id, exposed as assetId.
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