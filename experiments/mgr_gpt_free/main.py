"""
Główny plik aplikacji FastAPI dla systemu Finance Track.
Zawiera konfigurację lifespan oraz inicjalizację bazy danych.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session, engine
from models import Base
from schemas import FinancialAsset, FinancialAssetCreate
from crud import get_assets, create_asset


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Zarządzanie cyklem życia aplikacji (startup/shutdown).

    Przy starcie:
    - Tworzy tabele w bazie danych, jeśli nie istnieją.
    - Zapewnia zgodność struktury z modelem (w tym klucz główny asset_id).
    """
    try:
        async with engine.begin() as conn:
            # Tworzenie tabel na podstawie modeli ORM
            await conn.run_sync(Base.metadata.create_all)

        print("Baza danych gotowa (tabela financial_assets, PK: asset_id).")

        yield

    finally:
        # Możliwe miejsce na cleanup w przyszłości
        print("Zamykanie aplikacji Finance Track.")


# Inicjalizacja aplikacji z użyciem lifespan
app = FastAPI(
    title="Finance Track API",
    lifespan=lifespan,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Generator dostarczający sesję bazy danych (Dependency Injection).
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


@app.get("/status")
async def healthcheck() -> dict:
    """
    Endpoint testowy sprawdzający status aplikacji i bazy danych.
    """
    return {
        "status": "ok",
        "database": "connected",
    }


@app.get("/assets", response_model=List[FinancialAsset])
async def read_assets(
    db: AsyncSession = Depends(get_db),
) -> List[FinancialAsset]:
    """
    Endpoint zwracający listę wszystkich aktywów finansowych.
    """
    try:
        return await get_assets(db)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Błąd podczas pobierania danych",
        )


@app.post("/assets", response_model=FinancialAsset, status_code=201)
async def add_asset(
    asset_in: FinancialAssetCreate,
    db: AsyncSession = Depends(get_db),
) -> FinancialAsset:
    """
    Endpoint umożliwiający dodanie nowego aktywa finansowego.
    """
    try:
        return await create_asset(db, asset_in)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Błąd podczas zapisu danych",
        )