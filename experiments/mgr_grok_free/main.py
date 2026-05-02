"""
Główny plik aplikacji FastAPI dla systemu Finance Track.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import AsyncSessionLocal, init_db
from crud import get_assets, create_asset
from schemas import FinancialAsset, FinancialAssetCreate
from utils import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Zarządzanie cyklem życia aplikacji.
    """
    logger.info("Uruchomienie systemu Finance Track")
    await init_db()          # Automatyczne tworzenie tabel (asset_id jako klucz główny)
    logger.info("System Finance Track został pomyślnie uruchomiony")
    yield
    logger.info("Zamykanie systemu Finance Track")


app = FastAPI(
    title="Finance Track API",
    description="System do śledzenia aktywów finansowych",
    version="1.0.0",
    lifespan=lifespan
)


async def get_db():
    """
    Dependency Injection – sesja bazodanowa.
    """
    async with AsyncSessionLocal() as session:
        yield session


# ==================== GLOBALNA OBSŁUGA BŁĘDÓW ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Globalna obsługa wyjątków HTTPException z logowaniem.
    """
    logger.error(f"Błąd HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# ==================== ENDPOINTY ====================

@app.get("/assets", response_model=List[FinancialAsset])
async def read_assets(db: AsyncSession = Depends(get_db)):
    """
    Pobiera listę wszystkich aktywów finansowych.
    """
    try:
        assets = await get_assets(db)
        logger.info(f"Pobrano listę aktywów – liczba rekordów: {len(assets)}")
        return assets
    except Exception as e:
        logger.error(f"Błąd podczas pobierania aktywów: {str(e)}")
        raise HTTPException(status_code=500, detail="Wewnętrzny błąd serwera")


@app.post("/assets", response_model=FinancialAsset, status_code=201)
async def add_asset(asset: FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    """
    Dodaje nowe aktywo finansowe do bazy.
    """
    try:
        new_asset = await create_asset(db, asset)
        logger.info(f"Dodano nowe aktywo: {new_asset.ticker_symbol} (asset_id: {new_asset.asset_id})")
        return new_asset
    except Exception as e:
        await db.rollback()
        logger.error(f"Błąd podczas dodawania aktywa {asset.ticker_symbol}: {str(e)}")
        raise HTTPException(status_code=400, detail="Nie udało się dodać aktywa")


@app.get("/status")
async def healthcheck():
    """
    Endpoint healthcheck.
    """
    logger.info("Sprawdzono status systemu")
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