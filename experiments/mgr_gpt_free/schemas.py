"""
Pydantic schemas for Finance Track system.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FinancialAssetBase(BaseModel):
    """
    Base schema for financial assets.
    """

    ticker_symbol: str = Field(
        ...,
        pattern=r"^[A-Z]{1,5}$",
    )

    last_price: float = Field(
        ...,
        ge=0,
    )

    market_cap: int

    last_updated: Optional[datetime] = None


class FinancialAssetCreate(FinancialAssetBase):
    """
    Schema for asset creation.
    """
    pass


class FinancialAsset(FinancialAssetBase):
    """
    Schema for asset response.
    """

    asset_id: str

    model_config = ConfigDict(from_attributes=True)


class AnalyticsResponse(BaseModel):
    """
    Schema for analytics endpoint response.
    """

    ticker_symbol: str

    moving_average_30d: float

    rsi_14: float