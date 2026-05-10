from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import settings

# The engine pulls the DATABASE_URL dynamically from the Settings instance.
# echo=False prevents SQL queries from flooding the console logs.
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Asynchronous session factory configured for SQLAlchemy 2.0+
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)