from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import asc, desc
import models

async def get_assets(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 10, 
    min_price: float = None, 
    sort_by: str = "ticker_symbol"
):
    """
    Pobiera listę aktywów z obsługą paginacji, filtrowania ceny i sortowania.
    """
    # Podstawowe zapytanie
    query = select(models.FinancialAsset)

    # Filtrowanie po cenie minimalnej, jeśli podano
    if min_price is not None:
        query = query.where(models.FinancialAsset.last_price >= min_price)

    # Obsługa sortowania dynamicznego
    # Sprawdzamy, czy kolumna istnieje w modelu, aby uniknąć błędów
    if hasattr(models.FinancialAsset, sort_by):
        column = getattr(models.FinancialAsset, sort_by)
        query = query.order_by(column)
    else:
        # Domyślne sortowanie po tickerze
        query = query.order_by(models.FinancialAsset.ticker_symbol)

    # Paginacja: przesunięcie i limit
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()