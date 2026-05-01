import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from models import Base

# Konfiguracja adresu bazy danych (SQLite asynchronicznie)
DATABASE_URL = "sqlite+aiosqlite:///./finance.db"

# Tworzenie asynchronicznego silnika
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Ustawienie True pozwala na podgląd zapytań SQL w konsoli
)

# Fabryka asynchronicznych sesji
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    """Inicjalizacja struktur bazy danych."""
    async with engine.begin() as conn:
        # Tworzenie tabel na podstawie zdefiniowanych modeli
        await conn.run_sync(Base.metadata.create_all)