"""
Główna aplikacja FastAPI systemu Finance Track.
Udostępnia endpointy REST do zarządzania aktywami finansowymi.
"""

from typing import List

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# Importy modułów aplikacji (przy założeniu, że wszystkie są w jednym katalogu)
from database import async_session
from schemas import FinancialAsset, FinancialAssetCreate
from crud import get_assets, create_asset

# Inicjalizacja aplikacji FastAPI
app = FastAPI(title="Finance Track", version="0.1.0")


async def get_db() -> AsyncSession:
    """
    Generator zależności dostarczający asynchroniczną sesję bazodanową.
    Sesja jest automatycznie zamykana po obsłużeniu żądania.
    """
    async with async_session() as session:
        yield session


@app.get(
    "/assets",
    response_model=List[FinancialAsset],
    summary="Pobierz listę wszystkich aktywów",
)
async def read_assets(db: AsyncSession = Depends(get_db)):
    """
    Endpoint zwracający wszystkie rekordy z tabeli financial_assets.
    """
    try:
        assets = await get_assets()
    except Exception as e:
        # W przypadku nieoczekiwanego błędu bazy danych zwracamy 500
        raise HTTPException(
            status_code=500, detail=f"Błąd podczas pobierania aktywów: {str(e)}"
        )
    return assets


@app.post(
    "/assets",
    response_model=FinancialAsset,
    status_code=201,
    summary="Dodaj nowy aktyw finansowy",
)
async def create_new_asset(
    asset_data: FinancialAssetCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint tworzący nowy aktyw na podstawie dostarczonych danych.
    Klucz główny (asset_id) jest generowany automatycznie.
    """
    try:
        new_asset = await create_asset(asset_data)
    except ValueError as e:
        # Błędy walidacji biznesowej (np. duplikat tickera) zwracamy jako 409 Conflict
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        # Ogólna obsługa nieoczekiwanych błędów
        raise HTTPException(
            status_code=500, detail=f"Nieoczekiwany błąd serwera: {str(e)}"
        )
    return new_asset