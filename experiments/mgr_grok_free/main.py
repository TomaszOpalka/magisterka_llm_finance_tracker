"""
Główny plik aplikacji FastAPI dla systemu Finance Track.
"""

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import AsyncSessionLocal
from crud import get_assets, create_asset
from schemas import FinancialAsset, FinancialAssetCreate


app = FastAPI(
    title="Finance Track API",
    description="System do śledzenia aktywów finansowych",
    version="1.0.0"
)


# Asynchroniczny generator sesji bazodanowej
async def get_db():
    """
    Dependency Injection – dostarcza sesję bazodanową do endpointów.
    """
    async with AsyncSessionLocal() as session:
        yield session
        # Sesja zostanie automatycznie zamknięta po wyjściu z kontekstu


@app.get("/assets", response_model=List[FinancialAsset])
async def read_assets(db: AsyncSession = Depends(get_db)):
    """
    Endpoint zwracający listę wszystkich aktywów finansowych.
    """
    try:
        assets = await get_assets(db)
        return assets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas pobierania aktywów: {str(e)}")


@app.post("/assets", response_model=FinancialAsset, status_code=201)
async def add_asset(asset: FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    """
    Endpoint dodający nowe aktywo finansowe do bazy.
    """
    try:
        new_asset = await create_asset(db, asset)
        return new_asset
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Błąd podczas dodawania aktywa: {str(e)}")


@app.get("/")
async def root():
    """
    Podstawowy endpoint powitalny.
    """
    return {"message": "Witaj w systemie Finance Track API!"}