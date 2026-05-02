from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List

# Importujemy engine z database.py do obsługi procesu tworzenia tabel
from database import AsyncSessionLocal, engine
import models
import crud
import schemas


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Zarządza cyklem życia aplikacji FastAPI (startup i shutdown).
    Gwarantuje, że niezbędne tabele zostaną utworzone przed przyjęciem żądań.
    """
    # Akcje wykonywane podczas startu (startup)
    print("Uruchamianie aplikacji... Weryfikacja struktury bazy danych.")
    print("Sprawdzanie tabeli 'financial_assets' (oczekiwany klucz główny: 'asset_id').")
    
    # Wykorzystujemy engine.begin() do utworzenia asynchronicznej transakcji
    async with engine.begin() as conn:
        # Metoda run_sync wykonuje synchroniczną operację create_all bez blokowania pętli zdarzeń
        await conn.run_sync(models.Base.metadata.create_all)
        
    print("Inicjalizacja zakończona. Baza danych gotowa do pracy.")
    
    # Przekazanie kontroli do właściwej aplikacji
    yield
    
    # Akcje wykonywane podczas wyłączania aplikacji (shutdown)
    print("Zamykanie aplikacji... Czyszczenie zasobów silnika bazy danych.")
    await engine.dispose()


# Inicjalizacja instancji aplikacji FastAPI z wbudowanym lifespan
app = FastAPI(title="Finance Track API", lifespan=lifespan)


async def get_db():
    """
    Tworzy i zarządza cyklem życia sesji bazy danych dla każdego żądania (Dependency Injection).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@app.get("/status")
async def healthcheck():
    """
    Prosty endpoint diagnostyczny (Healthcheck).
    Potwierdza, że aplikacja jest uruchomiona, a baza danych gotowa.
    """
    return {"status": "ok", "database": "connected"}


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
        await db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="Instrument o podanym symbolu (ticker_symbol) już istnieje."
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, 
            detail="Wystąpił błąd wewnętrzny podczas zapisu aktywa."
        )