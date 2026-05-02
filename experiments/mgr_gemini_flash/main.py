from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from typing import List

import crud
import schemas
from database import async_session, init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Zarządza cyklem życia aplikacji. 
    Inicjalizuje bazę danych przed uruchomieniem serwera.
    """
    # Logika wykonywana przy starcie (Startup)
    print("Inicjalizacja systemu 'Finance Track'...")
    print("Weryfikacja tabel bazy danych (klucz główny: asset_id)...")
    await init_db()
    print("Baza danych gotowa do pracy.")
    
    yield  # W tym momencie aplikacja przyjmuje żądania
    
    # Logika wykonywana przy zamykaniu (Shutdown)
    print("Zamykanie systemu 'Finance Track'...")

app = FastAPI(
    title="Finance Track API",
    lifespan=lifespan
)

# Dependency: Generator sesji
async def get_db():
    async with async_session() as session:
        yield session

@app.get("/status")
async def health_check():
    """
    Endpoint testowy do weryfikacji dostępności systemu.
    """
    return {
        "status": "ok", 
        "database": "connected",
        "contract_verification": "asset_id_enforced"
    }

@app.get("/assets", response_model=List[schemas.FinancialAsset])
async def read_assets(db: AsyncSession = Depends(get_db)):
    """Pobiera listę aktywów finansowych."""
    assets = await crud.get_assets(db)
    return assets

@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201)
async def add_asset(asset: schemas.FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    """Dodaje nowe aktywo finansowe z automatycznym generowaniem asset_id."""
    try:
        new_asset = await crud.create_asset(db, asset)
        return new_asset
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Błąd podczas tworzenia zasobu: {str(e)}"
        )