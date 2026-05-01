import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import models
import schemas


async def get_assets(db: AsyncSession):
    """
    Pobiera wszystkie instrumenty finansowe z tabeli financial_assets.
    """
    # Budowa asynchronicznego zapytania
    query = select(models.FinancialAsset)
    
    # Wykonanie zapytania i pobranie wyników
    result = await db.execute(query)
    
    # Zwrócenie listy obiektów (scalars wypakowuje wyniki z krotek SQLAlchemy)
    return result.scalars().all()


async def create_asset(db: AsyncSession, asset: schemas.FinancialAssetCreate):
    """
    Tworzy nowy instrument finansowy i zapisuje go w bazie danych.
    Rozwiązuje problem braku autoinkrementacji dla klucza asset_id (String).
    """
    # Generowanie unikalnego klucza głównego asset_id (wersja UUID4 jako string)
    new_asset_id = str(uuid.uuid4())
    
    # Zamiana schematu Pydantic na słownik i wypakowanie danych do modelu SQLAlchemy
    db_asset = models.FinancialAsset(
        asset_id=new_asset_id,
        **asset.model_dump()
    )
    
    # Dodanie obiektu do sesji i zatwierdzenie transakcji
    db.add(db_asset)
    await db.commit()
    
    # Odświeżenie obiektu, aby upewnić się, że posiada zaktualizowane dane z bazy
    await db.refresh(db_asset)
    
    return db_asset