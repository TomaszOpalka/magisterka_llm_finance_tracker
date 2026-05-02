from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

import crud
import schemas
from database import async_session, init_db
from utils import logger
from exceptions import FinanceException, AssetNotFoundException  # Nowe importy

# --- Konfiguracja Lifespan (bez zmian względem poprzedniego kroku) ---
# ... (kod lifespan pozostaje taki sam)

app = FastAPI(title="Finance Track API")

# Globalny handler dla niestandardowych wyjątków FinanceException
@app.exception_handler(FinanceException)
async def finance_exception_handler(request: Request, exc: FinanceException):
    """
    Przechwytuje wyjątki biznesowe, loguje je i zwraca spójną odpowiedź JSON.
    """
    logger.error(f"Wyjątek biznesowy: {exc.message} | Status: {exc.status_code}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_type": exc.__class__.__name__,
            "detail": exc.message,
            "path": request.url.path
        }
    )

# Dependency: Generator sesji
async def get_db():
    async with async_session() as session:
        yield session

@app.get("/assets", response_model=List[schemas.FinancialAsset])
async def read_assets(db: AsyncSession = Depends(get_db)):
    """
    Pobiera listę aktywów. Rzuca AssetNotFoundException, jeśli baza jest pusta.
    """
    assets = await crud.get_assets(db)
    
    if not assets:
        # Logujemy brak danych, zwracając uwagę na brak rekordów
        logger.warning("Próba pobrania aktywów zakończona niepowodzeniem - brak danych.")
        raise AssetNotFoundException("W bazie danych nie zarejestrowano żadnych aktywów finansowych.")
    
    return assets

@app.get("/assets/{asset_id}", response_model=schemas.FinancialAsset)
async def read_asset_by_id(asset_id: str, db: AsyncSession = Depends(get_db)):
    """
    Przykładowy endpoint pobierający konkretne aktywo po asset_id.
    """
    # Logika CRUD dla pojedynczego elementu (założenie istnienia funkcji w crud.py)
    # W razie braku: raise AssetNotFoundException(f"Brak aktywa o asset_id: {asset_id}")
    pass

@app.post("/assets", response_model=schemas.FinancialAsset, status_code=201)
async def add_asset(asset: schemas.FinancialAssetCreate, db: AsyncSession = Depends(get_db)):
    try:
        new_asset = await crud.create_asset(db, asset)
        logger.info(f"Dodano zasób. asset_id: {new_asset.asset_id} | Ticker: {new_asset.ticker_symbol}")
        return new_asset
    except Exception as e:
        logger.error(f"Błąd podczas zapisu aktywa. Szczegóły: {str(e)}")
        raise FinanceException("Wystąpił nieoczekiwany błąd podczas tworzenia rekordu.")