from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import settings

# Added connect_args={"timeout": 15} to prevent "Database is locked" (503 errors)
# when multiple asynchronous requests hit the SQLite database simultaneously.
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=False,
    connect_args={"timeout": 15}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)