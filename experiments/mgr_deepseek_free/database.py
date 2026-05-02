"""
Moduł konfiguracji asynchronicznego połączenia z bazą danych SQLite.
Używa SQLAlchemy 2.0+ z silnikiem asynchronicznym (aiosqlite).
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Ścieżka do pliku bazy danych (względna – plik powstanie w katalogu aplikacji)
# Sterownik: aiosqlite (pip install aiosqlite)
DATABASE_URL = "sqlite+aiosqlite:///./finance.db"

# Asynchroniczny silnik SQLAlchemy – echo=True włącza logowanie SQL (przydatne przy rozwoju)
engine = create_async_engine(DATABASE_URL, echo=False)

# Fabryka sesji asynchronicznych – nie wygaszamy atrybutów po commit()
async_session = async_sessionmaker(engine, expire_on_commit=False)