"""
Moduł operacji CRUD dla tabeli financial_assets.
Obsługuje asynchroniczne sesje oraz parametry filtrowania, sortowania i paginacji.
"""

import uuid
from typing import Optional
from sqlalchemy import select, asc
from sqlalchemy.exc import IntegrityError

from database import async_session
from models import FinancialAsset
from schemas import FinancialAssetCreate

# Dozwolone pola do sortowania – zabezpieczenie przed niepoprawnym sort_by
ALLOWED_SORT_FIELDS = {
    "asset_id",
    "ticker_symbol",
    "last_price",
    "market_cap",
    "last_updated",
}


async def get_assets(
    skip: int = 0,
    limit: int = 10,
    min_price: Optional[float] = None,
    sort_by: Optional[str] = "ticker_symbol",
) -> list[FinancialAsset]:
    """
    Pobiera listę aktywów z możliwością pomijania (skip), ograniczania (limit),
    filtrowania po cenie minimalnej i dynamicznego sortowania.

    Argumenty:
        skip: Liczba rekordów do pominięcia (domyślnie 0).
        limit: Maksymalna liczba zwracanych rekordów (domyślnie 10, max 100).
        min_price: Opcjonalna minimalna cena – zwraca aktywa o cenie >= min_price.
        sort_by: Nazwa kolumny do sortowania rosnącego (domyślnie 'ticker_symbol').
                 Dozwolone: asset_id, ticker_symbol, last_price, market_cap, last_updated.

    Zwraca:
        Lista obiektów FinancialAsset spełniających kryteria.
    """
    async with async_session() as session:
        query = select(FinancialAsset)

        # Filtrowanie po cenie minimalnej
        if min_price is not None:
            query = query.where(FinancialAsset.last_price >= min_price)

        # Dynamiczne sortowanie – tylko dla bezpiecznych pól
        if sort_by not in ALLOWED_SORT_FIELDS:
            sort_by = "ticker_symbol"
        column = getattr(FinancialAsset, sort_by)
        query = query.order_by(asc(column))

        # Paginacja: pomijanie i ograniczanie wyników
        query = query.offset(skip).limit(limit)

        result = await session.execute(query)
        assets = result.scalars().all()
        return assets


async def create_asset(asset_data: FinancialAssetCreate) -> FinancialAsset:
    """
    Tworzy nowy rekord aktywu finansowego.

    Argumenty:
        asset_data: Zweryfikowany schemat Pydantic z danymi nowego aktywu.

    Zwraca:
        Utworzony obiekt FinancialAsset z nadanym asset_id.

    Wyjątki:
        ValueError: naruszenie integralności (np. duplikat ticker_symbol).
    """
    new_id = str(uuid.uuid4())

    async with async_session() as session:
        asset = FinancialAsset(
            asset_id=new_id,
            ticker_symbol=asset_data.ticker_symbol,
            last_price=asset_data.last_price,
            market_cap=asset_data.market_cap,
            last_updated=asset_data.last_updated,
        )
        session.add(asset)
        try:
            await session.commit()
            await session.refresh(asset)
        except IntegrityError as exc:
            await session.rollback()
            raise ValueError(
                f"Nie można utworzyć aktywu. Symbol '{asset_data.ticker_symbol}' "
                f"może już istnieć lub naruszono unikalność asset_id."
            ) from exc
        return asset