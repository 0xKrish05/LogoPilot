"""Sync DB session for Celery tasks (Celery workers don't run an event loop,
so tasks use a sync SQLAlchemy session against the same Postgres database)."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# asyncpg URL -> psycopg2 URL for the sync engine used by workers
_sync_url = settings.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")

engine = create_engine(_sync_url, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
