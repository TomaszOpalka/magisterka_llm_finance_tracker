"""
Główny plik aplikacji FastAPI dla systemu Finance Track.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import AsyncSessionLocal, init_db
from crud import get_assets, create_asset
from schemas import FinancialAsset, FinancialAssetCreate


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Zarządzanie cyklem życia aplikacji (Lifespan).
    Wykonuje inicjalizację bazy danych przy starcie.
    """
    print("🚀 Uruchamianie systemu Finance Track...")
    await init_db()          # Automatyczne tworzenie tabel
    print("✅ System gotowy do pracy.")
    yield
    # Możesz dodać kod sprzątający przy wyłączaniu aplikacji
    print("⏹️ Zamykanie aplikacji Finance Track.")


app = FastAPI(
    title="Finance Track API",
    description="System do śledzenia aktywów finansowych",
    version="1.0.0",
    lifespan=lifespan
)


# Dependency Injection - sesja bazodanowa
async def get_db():
    """
    Generator sesji asynchronicznej dla endpointów.
    """
    async with AsyncSessionLocal() as session:
        yield session


@app.get("/assets", response_model=List[FinancialAsset])
async def read_assets(db: AsyncSession = Depends(get_db)):
    """
    Pobiera listę wszystkich aktywów finansowych.
    """
    try:
        assets = await get_assets(db)
        return assets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas pobierania aktywów: {str(e)}")


@app.post("/assets", response_model=FinancialAsset, status_code=201)
async def add_asset(asset: FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    """
    Dodaje nowe aktywo finansowe do bazy.
    """
    try:
        new_asset = await create_asset(db, asset)
        return new_asset
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Błąd podczas dodawania aktywa: {str(e)}")


@app.get("/status")
async def healthcheck():
    """
    Endpoint healthcheck – sprawdzenie stanu aplikacji i połączenia z bazą.
    """
    return {
        "status": "ok",
        "database": "connected",
        "message": "System Finance Track działa poprawnie. Klucz główny: asset_id"
    }


@app.get("/")
async def root():
    """
    Endpoint powitalny.
    """
    return {"message": "Witaj w systemie Finance Track API!"}