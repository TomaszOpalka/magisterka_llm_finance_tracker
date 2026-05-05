from fastapi import FastAPI, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager
from typing import List, Optional

import crud
import schemas
from database import engine, async_session, init_db
from utils import logger
from exceptions import FinanceException, AssetNotFoundException

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Zarządza cyklem życia aplikacji.
    Inicjalizuje bazę danych oraz wykonuje asynchroniczne migracje struktury.
    """
    logger.info("--- Rozpoczęto uruchamianie systemu 'Finance Track' ---")
    
    # 1. Tworzenie tabel, jeśli nie istnieją
    await init_db()
    
    # 2. Asynchroniczna mini-migracja dla SQLite
    async with engine.begin() as conn:
        try:
            # Sprawdzenie istniejących kolumn w tabeli financial_assets
            result = await conn.execute(text("PRAGMA table_info(financial_assets)"))
            columns = [row[1] for row in result.fetchall()]
            
            # Dodanie kolumny last_updated, jeśli jej brakuje (migracja schematu)
            if "last_updated" not in columns:
                logger.info("Migracja: Dodawanie kolumny 'last_updated' do tabeli financial_assets.")
                await conn.execute(text("ALTER TABLE financial_assets ADD COLUMN last_updated DATETIME"))
                logger.info("Migracja kolumny zakończona sukcesem.")
            else:
                logger.info("Weryfikacja bazy: Struktura tabeli jest aktualna.")
                
            logger.info("Baza danych gotowa (Klucz główny: asset_id).")
        except Exception as e:
            logger.error(f"Błąd podczas weryfikacji struktury bazy: {str(e)}")

    yield  # Aplikacja działa i przyjmuje żądania
    
    logger.info("--- Zamykanie systemu 'Finance Track' ---")

# Inicjalizacja aplikacji FastAPI
app = FastAPI(
    title="Finance Track API",
    description="System do zarządzania danymi finansowymi z S&P 500",
    lifespan=lifespan
)

# --- Obsługa Wyjątków ---

@app.exception_handler(FinanceException)
async def finance_exception_handler(request: Request, exc: FinanceException):
    """
    Globalny handler dla niestandardowych wyjątków biznesowych.
    Loguje zdarzenie i zwraca ujednolicony format JSON.
    """
    logger.warning(f"Zablokowano żądanie: {exc.message} | Ścieżka: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_type": exc.__class__.__name__,
            "detail": exc.message,
            "path": request.url.path
        }
    )

# --- Zależności (Dependencies) ---

async def get_db():
    """Generator asynchronicznej sesji bazy danych."""
    async with async_session() as session:
        yield session

# --- Endpointy API ---

@app.get("/status", tags=["System"])
async def health_check():
    """Endpoint do szybkiej weryfikacji statusu aplikacji."""
    return {
        "status": "ok",
        "database": "connected",
        "schema_version": "2.0",
        "primary_key_contract": "asset_id"
    }

@app.get("/assets", response_model=List[schemas.FinancialAsset], tags=["Assets"])
async def read_assets(
    skip: int = Query(0, ge=0, description="Liczba pomijanych rekordów"),
    limit: int = Query(10, ge=1, le=100, description="Maksymalna liczba rekordów (max 100)"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimalna cena aktywa"),
    sort_by: str = Query(
        "ticker_symbol", 
        pattern="^(ticker_symbol|last_price|market_cap|asset_id)$",
        description="Pole, po którym nastąpi sortowanie"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Pobiera listę aktywów finansowych z obsługą paginacji, filtrowania i sortowania.
    Rzuca AssetNotFoundException w przypadku braku wyników.
    """
    assets = await crud.get_assets(
        db, 
        skip=skip, 
        limit=limit, 
        min_price=min_price, 
        sort_by=sort_by
    )
    
    if not assets:
        # Specjalna obsługa braku danych dla pierwszej strony
        if skip == 0:
            raise AssetNotFoundException("Baza danych nie zawiera żadnych aktywów.")
        return []
    
    logger.info(f"Pomyślnie zwrócono {len(assets)} rekordów (sortowanie po: {sort_by}).")
    return assets

@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201, tags=["Assets"])
async def add_asset(asset: schemas.FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    """
    Dodaje nowe aktywo finansowe do systemu.
    Automatycznie generuje asset_id oraz nadaje znacznik czasu last_updated.
    """
    try:
        new_asset = await crud.create_asset(db, asset)
        logger.info(f"Utworzono nowy zasób: {new_asset.ticker_symbol} (asset_id: {new_asset.asset_id})")
        return new_asset
    except Exception as e:
        logger.error(f"Błąd krytyczny przy tworzeniu aktywa: {str(e)}")
        raise FinanceException("Nie udało się zapisać aktywa. Sprawdź unikalność ticker_symbol.")

if __name__ == "__main__":
    import uvicorn
    # Uruchomienie serwera deweloperskiego
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)