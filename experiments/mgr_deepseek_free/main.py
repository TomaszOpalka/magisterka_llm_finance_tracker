"""
Główna aplikacja FastAPI systemu Finance Track.
Zarządza cyklem życia bazy danych, udostępnia endpointy REST oraz healthcheck.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, List

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect

# Lokalne importy (wszystkie pliki w tym samym katalogu)
from database import engine, async_session
from models import Base
from schemas import FinancialAsset, FinancialAssetCreate
from crud import get_assets, create_asset


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Zarządza zdarzeniami startu i zatrzymania aplikacji.
    Przy starcie automatycznie tworzy tabele (jeśli nie istnieją).
    """
    # --- STARTUP: tworzymy tabele, jeśli baza jest pusta ---
    async with engine.begin() as conn:
        # Sprawdzenie, czy tabela financial_assets już istnieje
        def check_tables_exist(sync_conn):
            inspector = inspect(sync_conn)
            return "financial_assets" in inspector.get_table_names()

        table_exists = await conn.run_sync(check_tables_exist)
        if not table_exists:
            # Tworzymy wszystkie tabele zdefiniowane w Base.metadata
            await conn.run_sync(Base.metadata.create_all)
            print("✅ UTWORZONO TABELE: financial_assets (i inne, jeśli istnieją w Base)")
        else:
            print("ℹ️  Tabela 'financial_assets' już istnieje – pomijam tworzenie.")

    yield  # Aplikacja działa

    # --- SHUTDOWN: zwalniamy zasoby silnika ---
    await engine.dispose()
    print("🛑 Silnik bazy danych został zamknięty.")


# Inicjalizacja aplikacji FastAPI z podpiętym lifespanem
app = FastAPI(
    title="Finance Track",
    version="0.1.0",
    lifespan=lifespan,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Wstrzykiwanie zależności – generator asynchronicznej sesji.
    Sesja jest automatycznie zamykana po zakończeniu żądania.
    """
    async with async_session() as session:
        yield session


# ---------- ENDPOINTY ----------

@app.get(
    "/status",
    response_model=Dict[str, str],
    summary="Healthcheck – stan aplikacji i połączenia z bazą",
)
async def status():
    """
    Prosty endpoint do monitorowania stanu serwera.
    Zwraca informację o statusie i łączności z bazą.
    """
    return {"status": "ok", "database": "connected"}


@app.get(
    "/assets",
    response_model=List[FinancialAsset],
    summary="Pobierz wszystkie aktywa finansowe",
)
async def read_assets(db: AsyncSession = Depends(get_db)):
    """
    Zwraca listę wszystkich rekordów z tabeli financial_assets.
    """
    try:
        assets = await get_assets()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Błąd pobierania aktywów: {str(e)}"
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
    Tworzy nowy wpis aktywu. Klucz główny `asset_id` generowany jest automatycznie.
    """
    try:
        new_asset = await create_asset(asset_data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Nieoczekiwany błąd: {str(e)}"
        )
    return new_asset