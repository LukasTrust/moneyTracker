"""
Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.routers import accounts, categories, data, dashboard, mappings, csv_import, recipients, budgets
from app.models.category import Category
from app.models.budget import Budget


def init_default_categories():
    """
    Initialize default categories if database is empty.
    Only runs once on first startup.
    """
    db = SessionLocal()
    try:
        # Check if categories already exist
        existing_count = db.query(Category).count()
        if existing_count > 0:
            print(f"ℹ️  {existing_count} categories already exist - skipping defaults")
            return
        
        # Default categories with German names and patterns
        default_categories = [
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
        
        # Create categories
        for cat_data in default_categories:
            category = Category(**cat_data)
            db.add(category)
        
        db.commit()
        print(f"✅ Created {len(default_categories)} default categories")
        
    except Exception as e:
        print(f"❌ Error creating default categories: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan - create tables on startup
    """
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    # Initialize default categories (only if database is empty)
    init_default_categories()
    
    yield
    
    # Cleanup (if needed)
    print("🛑 Shutting down application")


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


# Include routers
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
