from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Adres URL do asynchronicznej bazy SQLite (wymaga pakietu aiosqlite)
DATABASE_URL = "sqlite+aiosqlite:///finance.db"

# Utworzenie asynchronicznego silnika bazy danych
# echo=False wycisza logowanie zapytań SQL do konsoli (można zmienić na True w fazie debugowania)
engine = create_async_engine(DATABASE_URL, echo=False)

# Konfiguracja asynchronicznej fabryki sesji
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)