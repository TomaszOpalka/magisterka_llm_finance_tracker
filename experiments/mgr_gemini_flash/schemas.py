from pydantic import BaseModel, ConfigDict, Field, AliasGenerator
from pydantic.alias_generators import to_camel
from typing import Optional
from datetime import datetime

class BaseSchema(BaseModel):
    """
    Base data-validation controller enforcing inbound and outbound
    camelCase transformations globally while using native snake_case inside fields.
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
    # Hardcoded field-level overrides map current_market_price directly to lastPrice
    current_market_price: float = Field(
        validation_alias="lastPrice",
        serialization_alias="lastPrice"
    )
    market_cap: Optional[float] = None

class FinancialAssetCreate(FinancialAssetBase):
    """Data intake schema layer parsing camelCase payload structures."""
    pass

class FinancialAsset(FinancialAssetBase):
    """Outbound payload contract mapping data structures back to the public network."""
    asset_id: str
    last_updated: Optional[datetime] = None

class AssetAnalytics(BaseSchema):
    """Technical metadata indicator metrics wrapper."""
    moving_average_30d: Optional[float] = None
    rsi_14: Optional[float] = None

class AnalyticsResponse(BaseSchema):
    """Standardized response layout used to serve technical analysis calculations."""
    ticker_symbol: str
    moving_average_30d: Optional[float] = None
    rsi_14: Optional[float] = None
    data_points: int