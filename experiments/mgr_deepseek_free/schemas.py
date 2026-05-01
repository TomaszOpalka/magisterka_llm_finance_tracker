"""
Schematy Pydantic v2 dla warstwy walidacji danych systemu Finance Track.
Współpracują z modelem SQLAlchemy FinancialAsset.
"""

from pydantic import BaseModel, ConfigDict


class FinancialAssetBase(BaseModel):
    """
    Bazowy schemat zawierający wspólne pola dla aktywów finansowych.
    Pola odpowiadają strukturze tabeli financial_assets (bez klucza głównego).
    """
    ticker_symbol: str   # Symbol giełdowy, np. 'AAPL'
    last_price: float     # Ostatnia znana cena instrumentu
    market_cap: int       # Kapitalizacja rynkowa (duże liczby całkowite)


class FinancialAssetCreate(FinancialAssetBase):
    """
    Schemat używany podczas tworzenia nowego rekordu aktywu.
    Dziedziczy wszystkie pola z FinancialAssetBase.
    Nie zawiera identyfikatora – ten jest generowany/nadawany oddzielnie.
    """
    pass


class FinancialAsset(FinancialAssetBase):
    """
    Schemat do odczytu (odpowiedzi API) reprezentujący pełny rekord aktywu.
    Zawiera dodatkowe pole asset_id (klucz główny) oraz obsługę mapowania ORM.
    """
    asset_id: str  # Główny identyfikator aktywu (nigdy nie używamy samego 'id')

    # Konfiguracja umożliwiająca tworzenie instancji bezpośrednio z obiektów ORM
    model_config = ConfigDict(from_attributes=True)