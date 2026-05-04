from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class FinancialAssetBase(BaseModel):
    """
    Podstawowy schemat danych dla instrumentu finansowego.
    Wzbogacony o rygorystyczną walidację biznesową.
    """
    # Walidacja: od 1 do 5 wielkich liter alfabetu (np. AAPL, TSLA, O)
    ticker_symbol: str = Field(..., pattern=r'^[A-Z]{1,5}$')
    
    # Walidacja: cena nie może być ujemna (większa lub równa 0.0)
    last_price: float = Field(..., ge=0.0)
    
    market_cap: int
    
    # Nowe pole: data i czas, domyślnie None, aby pozwolić bazie danych wygenerować czas
    last_updated: Optional[datetime] = None


class FinancialAssetCreate(FinancialAssetBase):
    """Schemat używany podczas tworzenia aktywa."""
    pass


class FinancialAsset(FinancialAssetBase):
    """Pełny schemat reprezentujący instrument finansowy zwracany z API."""
    asset_id: str

    model_config = ConfigDict(from_attributes=True)