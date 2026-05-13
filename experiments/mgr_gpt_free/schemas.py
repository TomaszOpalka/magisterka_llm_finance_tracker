"""
Pydantic schemas for Finance Track.
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

TickerSymbol = Annotated[
    str,
    Field(
        min_length=1,
        max_length=5,
        pattern=r"^[A-Z]+$",
    ),
]


class FinancialAssetBase(BaseModel):
    """
    Base schema for financial assets.
    """

    ticker_symbol: TickerSymbol
    last_price: float = Field(ge=0)
    market_cap: int = Field(ge=0)
    last_updated: datetime | None = None


class FinancialAssetCreate(FinancialAssetBase):
    """
    Schema used for asset creation.
    """


class FinancialAsset(FinancialAssetBase):
    """
    Schema used for asset responses.
    """

    asset_id: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class AssetAnalytics(BaseModel):
    """
    Schema for analytics calculations.
    """

    ticker_symbol: str
    moving_average_30d: float | None
    rsi_14: float | None


class AnalyticsResponse(AssetAnalytics):
    """
    Final analytics response schema.
    """