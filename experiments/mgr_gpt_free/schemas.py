"""
Pydantic schemas for Finance Track.

Database layer:
- snake_case

API layer:
- camelCase
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic.alias_generators import to_camel


class CamelCaseModel(BaseModel):
    """
    Base schema with automatic camelCase conversion.
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

    current_market_price: float = Field(
        ge=0,
        validation_alias="lastPrice",
        serialization_alias="lastPrice",
    )

    market_cap: int = Field(ge=0)

    last_updated: datetime | None = None


class FinancialAssetCreate(FinancialAssetBase):
    """
    Schema for asset creation payloads.
    """


class FinancialAsset(CamelCaseModel):
    """
    Schema for financial asset responses.
    """

    asset_id: str = Field(
        serialization_alias="assetId",
    )

    ticker_symbol: TickerSymbol

    current_market_price: float = Field(
        serialization_alias="lastPrice",
    )

    market_cap: int

    last_updated: datetime | None = None


class AssetAnalytics(CamelCaseModel):
    """
    Schema for analytics responses.
    """

    ticker_symbol: str

    moving_average_30d: float | None

    rsi_14: float | None


class AnalyticsResponse(AssetAnalytics):
    """
    Final analytics response schema.
    """