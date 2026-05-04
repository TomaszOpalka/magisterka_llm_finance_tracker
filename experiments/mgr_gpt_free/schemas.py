"""
Schematy walidacji danych dla systemu Finance Track
z wykorzystaniem Pydantic v2.
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class FinancialAssetBase(BaseModel):
    """
    Bazowy schemat danych dla aktywów finansowych.
    """

    # Symbol giełdowy: tylko wielkie litery, długość 1–5 znaków
    ticker_symbol: Annotated[
        str,
        Field(
            pattern=r"^[A-Z]{1,5}$",
            description="Symbol giełdowy (1-5 wielkich liter)",
        ),
    ]

    # Cena nie może być ujemna
    last_price: Annotated[
        float,
        Field(ge=0, description="Cena >= 0"),
    ]

    # Kapitalizacja rynkowa
    market_cap: int

    # Data ostatniej aktualizacji (opcjonalna)
    last_updated: datetime | None = None


class FinancialAssetCreate(FinancialAssetBase):
    """
    Schemat używany do tworzenia nowych aktywów.
    """
    pass


class FinancialAsset(FinancialAssetBase):
    """
    Schemat do odczytu danych z bazy.
    """

    asset_id: str  # Klucz główny (zgodny z kontraktem)

    model_config = ConfigDict(from_attributes=True)