
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config.settings import settings

# Base class for all ORM models
class Base(DeclarativeBase):
    pass

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,           # Set True to log all SQL queries
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True    # Verify connection before using
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    """Get database session - use as context manager."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
