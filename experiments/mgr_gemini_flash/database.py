from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from models import Base
from config import settings  # Import centralnych ustawień

# Pobieranie adresu bazy danych z konfiguracji
DATABASE_URL = settings.DATABASE_URL

# Tworzenie asynchronicznego silnika
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Można również sparametryzować w config.py jeśli potrzebne
)

# Fabryka asynchronicznych sesji
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    """
    Inicjalizacja bazy danych. 
    Zapewnia utworzenie tabeli z kluczem głównym asset_id.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)