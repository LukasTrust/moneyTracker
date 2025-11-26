"""
Database Connection and Session Management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings
from app.utils import get_logger


# Create database engine
# For SQLite, we need to enable check_same_thread=False
is_sqlite = isinstance(settings.DATABASE_URL, str) and settings.DATABASE_URL.lower().startswith("sqlite://")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # Set to True for SQL debugging
    future=True,
    pool_pre_ping=True,
)

# Module logger
logger = get_logger("app.database")
logger.info("Created database engine (dialect=%s)", engine.dialect.name)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """
    Dependency to get database session
    
    Usage in FastAPI:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        logger.debug("Opening new DB session")
        yield db
    finally:
        db.close()
        logger.debug("Closed DB session")
