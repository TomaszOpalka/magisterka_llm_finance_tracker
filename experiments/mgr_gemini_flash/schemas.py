from pydantic import BaseModel, ConfigDict, Field, AliasGenerator
from pydantic.alias_generators import to_camel
from typing import Optional
from datetime import datetime

class BaseSchema(BaseModel):
    """
    Base schema configuration to handle global snake_case to camelCase mapping.
    Database remains snake_case; API uses camelCase.
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
    pass

class FinancialAsset(FinancialAssetBase):
    asset_id: str
    last_updated: Optional[datetime] = None

class AnalyticsResponse(BaseSchema):
    ticker_symbol: str
    moving_average_30d: Optional[float] = None
    rsi_14: Optional[float] = None
    data_points: int