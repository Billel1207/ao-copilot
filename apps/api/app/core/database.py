"""Sync database session — used by sync routes (team, etc.)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings

sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=15,
    pool_recycle=1800,
    pool_timeout=30,       # Timeout si pool épuisé (au lieu de bloquer indéfiniment)
)

SyncSessionLocal = sessionmaker(bind=sync_engine, autoflush=False, autocommit=False)


def get_db() -> Session:
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
