from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List

from database import AsyncSessionLocal, engine
import models
import crud
import schemas
from utils import logger, format_market_cap

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Zarządza cyklem życia aplikacji FastAPI (startup i shutdown).
    Teraz wyposażony w logowanie postępów.
    """
    logger.info("Uruchomienie systemu 'Finance Track'.")
    logger.info("Weryfikacja struktury bazy danych. Sprawdzanie obecności klucza głównego: 'asset_id'.")
    
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
        
    logger.info("Inicjalizacja zakończona. Baza danych jest zsynchronizowana i gotowa do pracy.")
    
    yield
    
    logger.info("Zamykanie aplikacji. Trwa bezpieczne czyszczenie zasobów silnika bazy danych.")
    await engine.dispose()

# Inicjalizacja instancji aplikacji FastAPI
app = FastAPI(title="Finance Track API", lifespan=lifespan)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Globalny handler przechwytujący wyjątki HTTPException.
    Rejestruje błąd w systemie logów przed wysłaniem odpowiedzi do klienta.
    """
    logger.error(f"Zgłoszono wyjątek HTTP {exc.status_code} na ścieżce {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

async def get_db():
    """Wstrzykiwanie zależności: generator sesji bazy danych."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@app.get("/status")
async def healthcheck():
    """Weryfikacja dostępności serwera."""
    return {"status": "ok", "database": "connected"}

@app.get("/assets", response_model=List[schemas.FinancialAsset])
async def read_assets(db: AsyncSession = Depends(get_db)):
    """Pobiera i zwraca listę wszystkich aktywów."""
    try:
        assets = await crud.get_assets(db)
        # Przykład opcjonalnego wykorzystania formatera z utils.py podczas logowania (nie modyfikuje schematu)
        logger.info(f"Pobrano listę aktywów. Zwracam {len(assets)} rekordów.")
        return assets
    except Exception as e:
        # Błąd nie-HTTP zostanie obsłużony klasycznie i zamieniony na HTTPException
        raise HTTPException(
            status_code=500, 
            detail="Wystąpił błąd wewnętrzny podczas pobierania aktywów."
        )

@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201)
async def add_asset(
    asset: schemas.FinancialAssetCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Dodaje nowe aktywo do bazy danych."""
    try:
        created_asset = await crud.create_asset(db, asset)
        
        # Weryfikacja Nomenklatury: Odwołanie do 'asset_id' w logach
        logger.info(
            f"Dodano nowe aktywo ({created_asset.ticker_symbol}). "
            f"Zarejestrowany klucz główny (asset_id): {created_asset.asset_id} | "
            f"Sformatowana kapitalizacja: {format_market_cap(created_asset.market_cap)}"
        )
        return created_asset
        
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="Instrument o podanym symbolu (ticker_symbol) już istnieje w systemie."
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, 
            detail="Wystąpił nieoczekiwany błąd podczas zapisu aktywa do bazy danych."
        )