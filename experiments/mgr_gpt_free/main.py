"""
Główny plik aplikacji FastAPI dla systemu Finance Track.
"""

from typing import AsyncGenerator, List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from database import async_session, engine
from models import Base
from schemas import FinancialAsset, FinancialAssetCreate
from crud import get_assets, create_asset

app = FastAPI(title="Finance Track API")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Generator dostarczający sesję bazy danych (Dependency Injection).
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


@app.on_event("startup")
async def on_startup() -> None:
    """
    Inicjalizacja bazy danych przy starcie aplikacji.
    Tworzy tabele, jeśli nie istnieją.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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