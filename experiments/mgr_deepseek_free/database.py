"""
Moduł konfiguracji asynchronicznego połączenia z bazą danych SQLite.
Korzysta z centralnych ustawień aplikacji (config.py).
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import settings  # Import konfiguracji

# Pobieramy URL bazy danych z ustawień (może nadpisany w .env)
DATABASE_URL = settings.DATABASE_URL

# Asynchroniczny silnik SQLAlchemy – logowanie SQL wyłączone (zmień echo=True dla debugowania)
engine = create_async_engine(DATABASE_URL, echo=False)

# Fabryka sesji asynchronicznych – nie wygaszamy atrybutów po commit()
async_session = async_sessionmaker(engine, expire_on_commit=False)