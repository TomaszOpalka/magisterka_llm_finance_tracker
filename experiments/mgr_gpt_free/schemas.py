"""
Pydantic schemas for Finance Track (API layer uses camelCase).
"""

from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, AliasGenerator
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """
    Base model enabling automatic camelCase serialization.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


TickerSymbol = Annotated[
    str,
    Field(
        min_length=1,
        max_length=5,
        pattern=r"^[A-Z]+$",
    ),
]


class FinancialAssetBase(CamelModel):
    """
    Base schema for financial asset API layer.
    """

    ticker_symbol: TickerSymbol
    last_price: float = Field(ge=0)
    market_cap: int = Field(ge=0)
    last_updated: Optional[datetime] = None


class FinancialAssetCreate(FinancialAssetBase):
    """
    Schema used for asset creation requests.
    """


class FinancialAsset(CamelModel):
    """
    Schema used for asset responses.
    """

    asset_id: str = Field(
        serialization_alias="assetId",
    )
    ticker_symbol: TickerSymbol
    last_price: float
    market_cap: int
    last_updated: Optional[datetime] = None


class AssetAnalytics(CamelModel):
    """
    Schema for analytics response.
    """

    ticker_symbol: str
    moving_average_30d: Optional[float]
    rsi_14: Optional[float]


class AnalyticsResponse(AssetAnalytics):
    """
    Final analytics API response schema.
    """