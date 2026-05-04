"""
Moduł zawierający schematy walidacji danych (Pydantic v2) dla systemu Finance Track.
"""

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class FinancialAssetBase(BaseModel):
    """
    Bazowy schemat aktywa finansowego z rygorystyczną walidacją.
    """

    ticker_symbol: str = Field(
        ...,
        pattern=r"^[A-Z]{1,5}$",
        description="Symbol tickera – tylko wielkie litery, 1-5 znaków",
        examples=["AAPL", "TSLA", "BTC"]
    )

    last_price: Optional[float] = Field(
        None,
        ge=0.0,
        description="Ostatnia cena aktywa (nie może być ujemna)"
    )

    market_cap: Optional[int] = Field(
        None,
        ge=0,
        description="Kapitalizacja rynkowa"
    )

    last_updated: Optional[datetime] = Field(
        None,
        description="Data i godzina ostatniej aktualizacji danych"
    )


class FinancialAssetCreate(FinancialAssetBase):
    """
    Schemat używany przy tworzeniu nowego aktywa finansowego.
    """

    pass


class FinancialAsset(FinancialAssetBase):
    """
    Schemat pełnego aktywa finansowego zwracanego do klienta (odczyt).
    """

    asset_id: str

    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True
    )