"""
Moduł operacji CRUD na tabeli financial_assets.
Korzysta z asynchronicznych sesji SQLAlchemy oraz schematów Pydantic.
"""

import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

# Importy absolutne – wszystkie moduły znajdują się w tym samym katalogu
from database import async_session
from models import FinancialAsset
from schemas import FinancialAssetCreate


async def get_assets() -> list[FinancialAsset]:
    """
    Pobiera wszystkie aktywa finansowe z bazy danych.

    Returns:
        Lista obiektów FinancialAsset (ORM) reprezentujących wszystkie rekordy.
    """
    async with async_session() as session:
        result = await session.execute(select(FinancialAsset))
        assets = result.scalars().all()
        return assets


async def create_asset(asset_data: FinancialAssetCreate) -> FinancialAsset:
    """
    Tworzy nowy rekord aktywu finansowego w bazie.

    Argumenty:
        asset_data: Schemat Pydantic z danymi nowego aktywu (bez asset_id).

    Zwraca:
        Utworzony obiekt FinancialAsset (ORM) z przypisanym asset_id.

    Wyjątki:
        ValueError: gdy zostanie naruszona integralność danych (np. duplikat ticker_symbol).
    """
    # Generujemy unikalny identyfikator UUID jako klucz główny.
    # W schemacie FinancialAssetCreate nie ma pola asset_id, więc tworzymy go tutaj.
    new_id = str(uuid.uuid4())

    async with async_session() as session:
        asset = FinancialAsset(
            asset_id=new_id,
            ticker_symbol=asset_data.ticker_symbol,
            last_price=asset_data.last_price,
            market_cap=asset_data.market_cap,
        )
        session.add(asset)
        try:
            await session.commit()
            await session.refresh(asset)
        except IntegrityError as exc:
            await session.rollback()
            raise ValueError(
                f"Nie można utworzyć aktywu: naruszono ograniczenie unikalności. "
                f"Symbol '{asset_data.ticker_symbol}' może już istnieć."
            ) from exc
        return asset