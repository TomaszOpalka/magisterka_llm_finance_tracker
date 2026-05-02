"""
Główna aplikacja FastAPI systemu Finance Track.
Udostępnia endpointy REST do zarządzania aktywami finansowymi.
Podczas startu automatycznie tworzy wymagane tabele w bazie danych.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, List

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# Importy modułów aplikacji (wszystkie pliki w jednym katalogu)
from database import engine, async_session
from models import Base
from schemas import FinancialAsset, FinancialAssetCreate
from crud import get_assets, create_asset


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Kontekst życia aplikacji: przy starcie tworzy tabele w bazie danych,
    przy zamykaniu zwalnia zasoby (silnik zostanie zamknięty przez async_session).
    """
    # Tworzymy tabele (jeśli nie istnieją) przed pierwszym żądaniem.
    # Używamy run_sync, ponieważ SQLAlchemy 2.0 nie udostępnia jeszcze
    # w pełni asynchronicznej wersji create_all.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Aplikacja działa

    # Opcjonalne porządki po zamknięciu – można np. pozbyć się puli połączeń.
    await engine.dispose()


# Inicjalizacja aplikacji FastAPI z podpiętym lifespanem
app = FastAPI(
    title="Finance Track",
    version="0.1.0",
    lifespan=lifespan,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Generator zależności dostarczający asynchroniczną sesję bazodanową.
    Typ zwracany to asynchroniczny generator, dlatego używamy AsyncGenerator.
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
    asset_id jest generowany automatycznie (UUID).
    """
    try:
        new_asset = await create_asset(asset_data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Nieoczekiwany błąd serwera: {str(e)}"
        )
    return new_asset