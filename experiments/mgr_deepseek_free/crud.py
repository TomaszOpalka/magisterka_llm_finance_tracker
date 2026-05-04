"""
Moduł operacji CRUD dla tabeli financial_assets.
Obsługuje asynchroniczne sesje i pełną integrację ze schematami Pydantic.
"""

import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database import async_session
from models import FinancialAsset
from schemas import FinancialAssetCreate


async def get_assets() -> list[FinancialAsset]:
    """
    Pobiera wszystkie aktywa finansowe z bazy danych.

    Returns:
        Lista obiektów FinancialAsset (ORM).
    """
    async with async_session() as session:
        result = await session.execute(select(FinancialAsset))
        return result.scalars().all()


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
            # Obsługa pola last_updated – jeśli nie podano, pozostanie None,
            # a baza automatycznie wstawi bieżącą datę/czas (server_default=func.now())
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