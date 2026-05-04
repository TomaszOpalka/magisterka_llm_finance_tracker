from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, Annotated
from datetime import datetime


class FinancialAssetBase(BaseModel):
    """
    Bazowy schemat z rygorystyczną walidacją polską i biznesową.
    """
    # Ticker: tylko wielkie litery, od 1 do 5 znaków (np. AAPL, BTC)
    ticker_symbol: Annotated[str, Field(pattern=r"^[A-Z]{1,5}$")]
    
    # Cena: nie może być ujemna
    last_price: Annotated[float, Field(ge=0)]
    
    # Kapitalizacja rynkowa
    market_cap: int
    
    # Pole czasu aktualizacji, domyślnie None
    last_updated: Optional[datetime] = None


class FinancialAssetCreate(FinancialAssetBase):
    """Schemat używany przy tworzeniu nowego zasobu."""
    pass


class FinancialAsset(FinancialAssetBase):
    """Pełny schemat odczytu danych z bazy."""
    asset_id: str

    model_config = ConfigDict(from_attributes=True)