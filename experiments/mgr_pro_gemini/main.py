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
import exceptions
from utils import logger, format_market_cap


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Zarządza cyklem życia aplikacji FastAPI (startup i shutdown)."""
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


@app.exception_handler(exceptions.FinanceException)
async def finance_exception_handler(request: Request, exc: exceptions.FinanceException):
    """
    Globalny handler dla autorskich wyjątków biznesowych (FinanceException).
    Zwraca ujednoliconą odpowiedź JSON do klienta i loguje zdarzenie.
    """
    # Logowanie błędu biznesowego z zachowaniem wymaganej nomenklatury (asset_id)
    logger.warning(
        f"Błąd biznesowy [{exc.status_code}] na ścieżce {request.url.path}: {exc.detail} "
        f"| Przypominacz systemowy: operacje bazują na identyfikatorze 'asset_id'."
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Globalny handler przechwytujący standardowe wyjątki HTTPException."""
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
    """
    Pobiera i zwraca listę wszystkich aktywów.
    Zgłasza błąd AssetNotFoundException, jeśli baza jest pusta.
    """
    try:
        assets = await crud.get_assets(db)
    except Exception as e:
        # W przypadku problemu z samym zapytaniem do bazy rzucamy nowy błąd
        raise exceptions.DatabaseConnectionException()
        
    # Weryfikacja czy lista nie jest pusta
    if not assets:
        raise exceptions.AssetNotFoundException(
            detail="Brak danych. Nie odnaleziono żadnego instrumentu (żaden 'asset_id' nie figuruje w bazie)."
        )

    logger.info(f"Pobrano listę aktywów. Zwracam {len(assets)} rekordów.")
    return assets


@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201)
async def add_asset(
    asset: schemas.FinancialAssetCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Dodaje nowe aktywo do bazy danych."""
    try:
        created_asset = await crud.create_asset(db, asset)
        
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
        raise exceptions.DatabaseConnectionException(
            detail="Wystąpił nieoczekiwany błąd podczas zapisu aktywa do bazy danych."
        )