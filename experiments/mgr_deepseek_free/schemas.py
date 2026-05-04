"""
Schematy Pydantic v2 dla systemu Finance Track.
Zawierają rygorystyczną walidację danych finansowych.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

# (Alternatywnie z Annotated, ale Field jest czytelniejszy)
class FinancialAssetBase(BaseModel):
    """
    Bazowy schemat wspólny dla tworzenia i odczytu.
    Pola odpowiadają strukturze tabeli financial_assets.
    """

    # Symbol giełdowy – tylko wielkie litery, długość 1-5 znaków
    ticker_symbol: str = Field(
        ...,
        pattern=r"^[A-Z]{1,5}$",
        description="Symbol giełdowy (1-5 wielkich liter), np. AAPL",
    )

    # Ostatnia cena – nie może być ujemna
    last_price: float = Field(..., ge=0, description="Ostatnia cena instrumentu (>=0)")

    # Kapitalizacja rynkowa (duże liczby całkowite)
    market_cap: int = Field(..., description="Kapitalizacja rynkowa w jednostkach bazowych")

    # Data ostatniej aktualizacji – domyślnie brak (None), ustawiana przez bazę
    last_updated: datetime | None = Field(
        default=None,
        description="Data i czas ostatniej aktualizacji rekordu",
    )


class FinancialAssetCreate(FinancialAssetBase):
    """
    Schemat do tworzenia nowego aktywu.
    Dziedziczy wszystkie pola z FinancialAssetBase.
    """
    pass


class FinancialAsset(FinancialAssetBase):
    """
    Schemat do odczytu, zawiera klucz główny asset_id.
    Współpracuje z ORM (from_attributes=True).
    """
    asset_id: str = Field(..., description="Główny identyfikator aktywu (UUID)")

    model_config = ConfigDict(from_attributes=True)