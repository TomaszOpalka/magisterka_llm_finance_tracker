from pydantic import BaseModel, ConfigDict


class FinancialAssetBase(BaseModel):
    """
    Podstawowy schemat danych dla instrumentu finansowego.
    Zawiera wspólne pola używane zarówno przy tworzeniu, jak i odczycie danych.
    """
    ticker_symbol: str
    last_price: float
    market_cap: int


class FinancialAssetCreate(FinancialAssetBase):
    """
    Schemat używany podczas operacji tworzenia nowego instrumentu.
    Dziedziczy pola z klasy bazowej. Na tym etapie asset_id zazwyczaj
    nie jest jeszcze wymagane (generowane przez system/bazę).
    """
    pass


class FinancialAsset(FinancialAssetBase):
    """
    Pełny schemat reprezentujący instrument finansowy zwracany z API.
    Zawiera unikalny identyfikator asset_id.
    """
    asset_id: str

    # Konfiguracja Pydantic v2 dla współpracy z modelami ORM (np. SQLAlchemy)
    model_config = ConfigDict(from_attributes=True)


# Komentarz techniczny:
# Użycie model_config = ConfigDict(from_attributes=True) pozwala Pydantic 
# na automatyczne mapowanie obiektów SQLAlchemy na powyższy schemat, 
# nawet jeśli dane nie są słownikiem (dict), lecz obiektami klas.