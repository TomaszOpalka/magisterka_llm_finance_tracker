"""
Definicje modeli ORM dla systemu Finance Track.
"""

from sqlalchemy import BigInteger, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Klasa bazowa dla wszystkich modeli ORM.
    """
    pass


class FinancialAsset(Base):
    """
    Model reprezentujący aktywa finansowe.
    """

    __tablename__ = "financial_assets"

    # Unikalny identyfikator aktywa (Primary Key)
    asset_id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
    )

    # Symbol giełdowy (unikalny i indeksowany)
    ticker_symbol: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    # Ostatnia znana cena aktywa
    last_price: Mapped[float] = mapped_column(
        Float,
        nullable=True,
    )

    # Kapitalizacja rynkowa (duże liczby całkowite)
    market_cap: Mapped[int] = mapped_column(
        BigInteger,
        nullable=True,
    )