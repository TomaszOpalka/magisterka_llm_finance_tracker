"""
Moduł konfiguracji asynchronicznego połączenia z bazą danych SQLite.
Używa SQLAlchemy 2.0+ z silnikiem asynchronicznym (aiosqlite).
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Ścieżka do pliku bazy danych SQLite (w tym samym katalogu co aplikacja)
# Wymaga sterownika aiosqlite: pip install aiosqlite
DATABASE_URL = "sqlite+aiosqlite:///./finance.db"

# Tworzymy asynchroniczny silnik bazodanowy.
# echo=False wyłącza logowanie zapytań SQL – zmień na True podczas debugowania.
engine = create_async_engine(DATABASE_URL, echo=False)

# Fabryka sesji asynchronicznych.
# expire_on_commit=False zapobiega wygasaniu atrybutów obiektów po commit(),
# co jest wygodne w aplikacjach asynchronicznych.
async_session = async_sessionmaker(engine, expire_on_commit=False)