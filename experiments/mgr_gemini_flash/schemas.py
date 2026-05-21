from pydantic import BaseModel, ConfigDict, AliasGenerator
from pydantic.alias_generators import to_camel
from typing import Optional
from datetime import datetime

class BaseSchema(BaseModel):
    """
    Core schema pattern for global snake_case <-> camelCase transformations.
    Configures Pydantic v2 to accept inbound camelCase payloads and emit 
    outbound camelCase responses, while mapping internally to snake_case.
    """
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=to_camel,
            serialization_alias=to_camel,
        ),
        populate_by_name=True,
        from_attributes=True
    )

class FinancialAssetBase(BaseSchema):
    ticker_symbol: str
    last_price: float
    market_cap: Optional[float] = None

class FinancialAssetCreate(FinancialAssetBase):
    """
    Handles incoming JSON payloads for asset registration.
    Strictly expects inbound camelCase keys (tickerSymbol, lastPrice, marketCap).
    """
    pass

class FinancialAsset(FinancialAssetBase):
    """
    Represents an asset record emitted by the API.
    Transforms snake_case properties to camelCase (assetId, lastUpdated).
    """
    asset_id: str
    last_updated: Optional[datetime] = None

class AssetAnalytics(BaseSchema):
    """Technical sub-metrics for an asset record."""
    moving_average_30d: Optional[float] = None
    rsi_14: Optional[float] = None

class AnalyticsResponse(BaseSchema):
    """Unified response envelope for technical indicator data streams."""
    ticker_symbol: str
    moving_average_30d: Optional[float] = None
    rsi_14: Optional[float] = None
    data_points: int