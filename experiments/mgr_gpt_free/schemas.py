"""
Pydantic schemas for Finance Track.

API layer uses camelCase.
Database layer remains snake_case.
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic.alias_generators import to_camel


class CamelCaseModel(BaseModel):
    """
    Base schema enabling automatic camelCase conversion
    for both request and response payloads.
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


class FinancialAssetBase(CamelCaseModel):
    """
    Base financial asset schema.
    """

    ticker_symbol: TickerSymbol
    last_price: float = Field(ge=0)
    market_cap: int = Field(ge=0)
    last_updated: datetime | None = None


class FinancialAssetCreate(FinancialAssetBase):
    """
    Schema used for inbound asset creation payloads.

    Accepted JSON example:

    {
        "tickerSymbol": "AAPL",
        "lastPrice": 120.5,
        "marketCap": 1000000000
    }
    """


class FinancialAsset(CamelCaseModel):
    """
    Schema used for outbound asset responses.
    """

    asset_id: str
    ticker_symbol: TickerSymbol
    last_price: float
    market_cap: int
    last_updated: datetime | None = None


class AssetAnalytics(CamelCaseModel):
    """
    Schema for analytics response payload.
    """

    ticker_symbol: str
    moving_average_30d: float | None
    rsi_14: float | None


class AnalyticsResponse(AssetAnalytics):
    """
    Final analytics response schema.
    """