"""
Moduł zawierający schematy walidacji danych (Pydantic v2) dla systemu Finance Track.
Schematy są używane do walidacji danych wejściowych oraz serializacji odpowiedzi API.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional


class FinancialAssetBase(BaseModel):
    """
    Bazowy schemat aktywa finansowego.
    Zawiera pola wspólne dla tworzenia i odczytu danych.
    """

    ticker_symbol: str
    last_price: Optional[float] = None
    market_cap: Optional[int] = None


class FinancialAssetCreate(FinancialAssetBase):
    """
    Schemat używany przy tworzeniu nowego aktywa finansowego.
    Dziedziczy wszystkie pola z FinancialAssetBase.
    """

    pass


class FinancialAsset(FinancialAssetBase):
    """
    Schemat pełnego aktywa finansowego zwracanego do klienta (odczyt).
    Zawiera dodatkowe pole asset_id generowane przez bazę danych.
    """

    asset_id: str

    model_config = ConfigDict(
        from_attributes=True,   # Umożliwia konwersję z modeli SQLAlchemy (ORM)
        arbitrary_types_allowed=True
    )