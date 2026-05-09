import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from logger import get_logger

logger = get_logger(__name__, "backend.log")

# ─── Database Setup ───────────────────────────────────────────────────────────

_DB_DIR = "/app/data"
_DB_URL = f"sqlite:///{_DB_DIR}/backend_app.db"

os.makedirs(_DB_DIR, exist_ok=True)
logger.debug("Database directory ensured: %s", _DB_DIR)

engine = create_engine(_DB_URL, connect_args={"check_same_thread": False})
logger.info("Database engine created: %s", _DB_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ─── Dependency ───────────────────────────────────────────────────────────────

def get_db():
    """Yields a SQLAlchemy session and ensures it is closed after use."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        logger.exception("Unexpected error during database session; rolling back.")
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("Database session closed.")
