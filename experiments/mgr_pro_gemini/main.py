from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List

from database import AsyncSessionLocal
import crud
import schemas

# Inicjalizacja instancji aplikacji FastAPI
app = FastAPI(title="Finance Track API")


# Generator sesji bazodanowej - Wstrzykiwanie Zależności (Dependency Injection)
async def get_db():
    """
    Tworzy i zarządza cyklem życia sesji bazy danych dla każdego żądania.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@app.get("/assets", response_model=List[schemas.FinancialAsset])
async def read_assets(db: AsyncSession = Depends(get_db)):
    """
    Endpoint obsługujący metodę GET.
    Zwraca listę wszystkich aktywów w systemie.
    """
    try:
        assets = await crud.get_assets(db)
        return assets
    except Exception as e:
        # Ogólna obsługa nieoczekiwanych błędów
        raise HTTPException(
            status_code=500, 
            detail="Wystąpił błąd podczas pobierania aktywów."
        )


@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201)
async def add_asset(
    asset: schemas.FinancialAssetCreate, 
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint obsługujący metodę POST.
    Przyjmuje dane zdefiniowane w FinancialAssetCreate i tworzy nowe aktywo.
    Zwraca kod 201 (Created) po pomyślnym wykonaniu.
    """
    try:
        created_asset = await crud.create_asset(db, asset)
        return created_asset
    except IntegrityError:
        # Obsługa naruszenia unikalności (np. ticker_symbol, który już istnieje w bazie)
        await db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="Instrument o podanym symbolu (ticker_symbol) już istnieje."
        )
    except Exception as e:
        # Wycofanie transakcji w razie innego krytycznego błędu zapisu
        await db.rollback()
        raise HTTPException(
            status_code=500, 
            detail="Wystąpił błąd wewnętrzny podczas zapisu aktywa."
        )