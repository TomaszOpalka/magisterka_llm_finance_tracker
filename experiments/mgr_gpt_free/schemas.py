"""
Schematy walidacji danych dla systemu Finance Track
z wykorzystaniem biblioteki Pydantic v2.
"""

from pydantic import BaseModel, ConfigDict


class FinancialAssetBase(BaseModel):
    """
    Bazowy schemat danych dla aktywów finansowych.

    Zawiera wspólne pola używane przy tworzeniu i odczycie danych.
    """

    ticker_symbol: str  # Symbol giełdowy (np. AAPL)
    last_price: float  # Ostatnia cena aktywa
    market_cap: int  # Kapitalizacja rynkowa


class FinancialAssetCreate(FinancialAssetBase):
    """
    Schemat używany do tworzenia nowych aktywów finansowych.

    Dziedziczy wszystkie pola z klasy bazowej.
    """
    pass


class FinancialAsset(FinancialAssetBase):
    """
    Schemat używany do odczytu danych aktywów finansowych.

    Rozszerza schemat bazowy o identyfikator asset_id
    oraz umożliwia współpracę z obiektami ORM.
    """

    asset_id: str  # Unikalny identyfikator aktywa

    # Konfiguracja modelu dla Pydantic v2
    # Umożliwia tworzenie schematu na podstawie obiektów ORM (np. SQLAlchemy)
    model_config = ConfigDict(from_attributes=True)