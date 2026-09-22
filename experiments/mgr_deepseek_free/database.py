"""
Asynchroniczna konfiguracja silnika i sesji bazy danych dla Finance Track.
Wykorzystuje SQLAlchemy 2.0+ z aiosqlite.
Adres DATABASE_URL pobierany jest z centralnej konfiguracji (config.py).
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import settings

# Tworzymy asynchroniczny silnik na podstawie URL z ustawień
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Fabryka sesji – bez wygasania atrybutów po commit
async_session = async_sessionmaker(engine, expire_on_commit=False)