from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from typing import List

import crud
import schemas
from database import async_session, init_db
from utils import logger  # Import naszego loggera

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Zarządza startem i zatrzymaniem aplikacji z logowaniem zdarzeń."""
    logger.info("Rozpoczęto procedurę uruchamiania systemu 'Finance Track'.")
    try:
        await init_db()
        logger.info("Baza danych zainicjalizowana pomyślnie (klucz główny: asset_id).")
    except Exception as e:
        logger.error(f"KRYTYCZNY BŁĄD STARTU: {str(e)}")
        raise e
    
    yield
    
    logger.info("System 'Finance Track' zostaje wyłączony.")

app = FastAPI(title="Finance Track API", lifespan=lifespan)

# Globalna obsługa wyjątków HTTPException dla celów logowania
@app.exception_handler(HTTPException)
async def logging_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"Błąd HTTP: {exc.status_code} - {exc.detail} | Ścieżka: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

async def get_db():
    async with async_session() as session:
        yield session

@app.get("/status")
async def health_check():
    return {"status": "ok", "database": "connected"}

@app.get("/assets", response_model=List[schemas.FinancialAsset])
async def read_assets(db: AsyncSession = Depends(get_db)):
    assets = await crud.get_assets(db)
    logger.info(f"Pobrano listę {len(assets)} aktywów z bazy.")
    return assets

@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201)
async def add_asset(asset: schemas.FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    try:
        new_asset = await crud.create_asset(db, asset)
        logger.info(f"Pomyślnie dodano nowe aktywo: {new_asset.ticker_symbol} z asset_id: {new_asset.asset_id}")
        return new_asset
    except Exception as e:
        error_msg = f"Nieudana próba dodania aktywa {asset.ticker_symbol}: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)