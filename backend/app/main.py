"""
Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.routers import accounts, categories, data, dashboard, mappings, csv_import, recipients, budgets, recurring, comparison, import_history, transfers, insights
from app.utils import get_logger
from app.models.category import Category
from app.models.budget import Budget
import asyncio


DEFAULT_CATEGORIES = [
    {
        "name": "Lebensmittel",
        "color": "#10b981",
        "icon": "🛒",
        "mappings": {"patterns": ["REWE", "EDEKA", "ALDI", "LIDL", "Kaufland", "Netto", "Penny"]}
    },
    {
        "name": "Transport",
        "color": "#3b82f6",
        "icon": "🚗",
        "mappings": {"patterns": ["Tankstelle", "Shell", "Aral", "DB", "Deutsche Bahn", "MVG", "BVG"]}
    },
    {
        "name": "Wohnung",
        "color": "#f59e0b",
        "icon": "🏠",
        "mappings": {"patterns": ["Miete", "Strom", "Gas", "Wasser", "Stadtwerke", "Vonovia"]}
    },
    {
        "name": "Gehalt",
        "color": "#22c55e",
        "icon": "💰",
        "mappings": {"patterns": ["Gehalt", "Lohn", "Arbeitgeber"]}
    },
    {
        "name": "Online Shopping",
        "color": "#f97316",
        "icon": "📦",
        "mappings": {"patterns": ["Amazon", "Ebay", "Zalando", "Otto"]}
    },
    {
        "name": "Restaurant",
        "color": "#ef4444",
        "icon": "🍽️",
        "mappings": {"patterns": ["Restaurant", "Lieferando", "McDonald", "Burger King"]}
    },
    {
        "name": "Freizeit",
        "color": "#8b5cf6",
        "icon": "🎮",
        "mappings": {"patterns": ["Netflix", "Spotify", "Steam", "PlayStation", "Kino"]}
    },
    {
        "name": "Gesundheit",
        "color": "#ec4899",
        "icon": "💊",
        "mappings": {"patterns": ["Apotheke", "Arzt", "Krankenversicherung", "AOK", "TK"]}
    },
]


def init_default_categories():
    """Initialize default categories if database is empty.

    This function is intentionally synchronous and safe to run in a thread
    via `asyncio.to_thread(...)` from an async startup hook so it won't
    block the event loop during potentially slow database operations.
    """
    logger = get_logger("app.init")
    db = SessionLocal()
    try:
        # Check if categories already exist
        existing_count = db.query(Category).count()
        if existing_count > 0:
            logger.info("%d categories already exist - skipping defaults", existing_count)
            return

        for cat_data in DEFAULT_CATEGORIES:
            db.add(Category(**cat_data))

        db.commit()
        logger.info("Created %d default categories", len(DEFAULT_CATEGORIES))
    except Exception:
        logger.exception("Error creating default categories")
        try:
            db.rollback()
        except Exception:
            logger.debug("Rollback failed or session not available", exc_info=True)
    finally:
        try:
            db.close()
        except Exception:
            logger.debug("Closing DB session failed", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan - create tables on startup
    """
    # Create database tables in a thread to avoid blocking the event loop
    logger = get_logger("app.lifespan")
    try:
        await asyncio.to_thread(Base.metadata.create_all, bind=engine)
        logger.info("Database tables ensured/created")
    except Exception:
        logger.exception("Creating database tables failed")

    # Initialize default categories (only if database is empty) in a thread
    try:
        await asyncio.to_thread(init_default_categories)
        logger.info("Default categories initialization complete")
    except Exception:
        logger.exception("Initialization of default categories failed")
    
    yield
    
    # Cleanup (if needed)
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Money Tracker Backend API - Verwaltung von Konten, Transaktionen und Kategorien",
    lifespan=lifespan,
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
get_logger("app.main").info("CORS configured for origins: %s", settings.BACKEND_CORS_ORIGINS)


# Include routers
# Register recurring routes earlier so static paths are matched before
# generic account-id routes (prevents '/recurring-transactions' being
# interpreted as an account_id for routes like '/{account_id}/...').
app.include_router(
    recurring.router,
    prefix=f"{settings.API_V1_PREFIX}/accounts",
    tags=["recurring"]
)

app.include_router(
    accounts.router,
    prefix=f"{settings.API_V1_PREFIX}/accounts",
    tags=["accounts"]
)

app.include_router(
    categories.router,
    prefix=f"{settings.API_V1_PREFIX}/categories",
    tags=["categories"]
)

app.include_router(
    data.router,
    prefix=f"{settings.API_V1_PREFIX}/accounts",
    tags=["data"]
)

app.include_router(
    dashboard.router,
    prefix=f"{settings.API_V1_PREFIX}/dashboard",
    tags=["dashboard"]
)

app.include_router(
    mappings.router,
    prefix=f"{settings.API_V1_PREFIX}/accounts",
    tags=["mappings"]
)

app.include_router(
    csv_import.router,
    prefix=f"{settings.API_V1_PREFIX}/csv-import",
    tags=["csv-import"]
)

app.include_router(
    recipients.router,
    prefix=f"{settings.API_V1_PREFIX}/recipients",
    tags=["recipients"]
)

app.include_router(
    budgets.router,
    prefix=f"{settings.API_V1_PREFIX}/budgets",
    tags=["budgets"]
)


app.include_router(
    comparison.router,
    prefix=f"{settings.API_V1_PREFIX}/comparison",
    tags=["comparison"]
)

app.include_router(
    import_history.router,
    prefix=f"{settings.API_V1_PREFIX}/import-history",
    tags=["import-history"]
)

app.include_router(
    transfers.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["transfers"]
)

app.include_router(
    insights.router,
    prefix=f"{settings.API_V1_PREFIX}/insights",
    tags=["insights"]
)

# Log routes/routers summary
get_logger("app.main").info("Included routers; total routes: %d", len(app.routes))


@app.get("/")
async def root():
    """
    Root endpoint - health check
    """
    return {
        "message": "Money Tracker API",
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )
