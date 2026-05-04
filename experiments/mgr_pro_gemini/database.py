from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Importujemy instancję ustawień z nowego pliku konfiguracyjnego
from config import settings

# Utworzenie asynchronicznego silnika bazy danych z wykorzystaniem adresu URL z ustawień.
# echo=False wycisza logowanie zapytań SQL do konsoli.
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Konfiguracja asynchronicznej fabryki sesji
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)