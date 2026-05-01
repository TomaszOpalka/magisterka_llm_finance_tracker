"""
Warstwa operacji CRUD dla systemu Finance Track.
"""

from typing import List
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models import FinancialAsset
from schemas import FinancialAssetCreate


async def get_assets(db: AsyncSession) -> List[FinancialAsset]:
    """
    Pobiera wszystkie aktywa finansowe z bazy danych.

    :param db: Asynchroniczna sesja bazy danych
    :return: Lista obiektów FinancialAsset
    """
    try:
        result = await db.execute(select(FinancialAsset))
        assets = result.scalars().all()
        return assets
    except SQLAlchemyError as exc:
        # W przypadku błędu zwracamy wyjątek wyżej
        raise exc


async def create_asset(
    db: AsyncSession,
    asset_in: FinancialAssetCreate,
) -> FinancialAsset:
    """
    Tworzy nowe aktywo finansowe w bazie danych.

    :param db: Asynchroniczna sesja bazy danych
    :param asset_in: Dane wejściowe do utworzenia aktywa
    :return: Utworzony obiekt FinancialAsset
    """
    try:
        # Generowanie unikalnego identyfikatora asset_id
        new_asset = FinancialAsset(
            asset_id=str(uuid4()),
            ticker_symbol=asset_in.ticker_symbol,
            last_price=asset_in.last_price,
            market_cap=asset_in.market_cap,
        )

        db.add(new_asset)
        await db.commit()
        await db.refresh(new_asset)

        return new_asset

    except SQLAlchemyError as exc:
        # Wycofanie transakcji w przypadku błędu
        await db.rollback()
        raise exc