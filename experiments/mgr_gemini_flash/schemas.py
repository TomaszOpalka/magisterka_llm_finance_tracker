from pydantic import BaseModel, ConfigDict
from typing import Optional


class FinancialAssetBase(BaseModel):
    """
    Bazowy schemat zawierający wspólne pola dla aktywów finansowych.
    Używany jako fundament dla innych modeli.
    """
    ticker_symbol: str
    last_price: float
    market_cap: int


class FinancialAssetCreate(FinancialAssetBase):
    """
    Schemat używany podczas operacji tworzenia nowego aktywa (POST).
    Na tym etapie asset_id zazwyczaj nie jest jeszcze znane lub jest generowane.
    """
    # Można tu dodać dodatkowe walidacje specyficzne dla procesu tworzenia
    pass


class FinancialAsset(FinancialAssetBase):
    """
    Schemat używany do zwracania danych z API (odczyt).
    Zawiera unikalny identyfikator asset_id.
    """
    asset_id: str

    # Konfiguracja Pydantic v2 dla współpracy z ORM (np. SQLAlchemy)
    model_config = ConfigDict(from_attributes=True)


class FinancialAssetUpdate(BaseModel):
    """
    Opcjonalny schemat do aktualizacji danych (PATCH).
    Wszystkie pola są opcjonalne, aby umożliwić częściową aktualizację.
    """
    ticker_symbol: Optional[str] = None
    last_price: Optional[float] = None
    market_cap: Optional[int] = None