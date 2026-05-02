from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from models import Base

DATABASE_URL = "sqlite+aiosqlite:///./finance.db"

engine = create_async_engine(DATABASE_URL, echo=False)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    """
    Tworzy wszystkie tabele zdefiniowane w modelach (w tym financial_assets).
    Wykorzystuje klucz główny 'asset_id' zgodnie ze schematem.
    """
    async with engine.begin() as conn:
        # run_sync jest wymagane do operacji na metadanych w silniku asynchronicznym
        await conn.run_sync(Base.metadata.create_all)