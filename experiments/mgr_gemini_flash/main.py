from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

import crud
import schemas
from database import async_session, init_db

app = FastAPI(title="Finance Track API")

# Dependency: Generator sesji bazy danych
async def get_db():
    """
    Tworzy nową asynchroniczną sesję dla każdego zapytania 
    i zamyka ją po zakończeniu operacji.
    """
    async with async_session() as session:
        yield session

@app.on_event("startup")
async def startup():
    """
    Inicjalizacja bazy danych (tworzenie tabel) przy starcie aplikacji.
    """
    await init_db()

@app.get("/assets", response_model=List[schemas.FinancialAsset])
async def read_assets(db: AsyncSession = Depends(get_db)):
    """
    Endpoint zwracający listę wszystkich aktywów finansowych.
    """
    assets = await crud.get_assets(db)
    return assets

@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201)
async def add_asset(asset: schemas.FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    """
    Endpoint do dodawania nowego aktywa. 
    Sprawdza, czy asset_id został poprawnie wygenerowany i zapisany.
    """
    try:
        new_asset = await crud.create_asset(db, asset)
        return new_asset
    except Exception as e:
        # Podstawowa obsługa błędów (np. naruszenie unikalności ticker_symbol)
        raise HTTPException(status_code=400, detail=f"Błąd podczas tworzenia aktywa: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)