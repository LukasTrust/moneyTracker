"""
Main FastAPI Application
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.openapi.utils import get_openapi

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.routers import accounts, categories, data, dashboard, mappings, csv_import, recipients, budgets, recurring, comparison, import_history, transfers, insights
from app.utils import get_logger
from app.models.category import Category
from app.models.budget import Budget
from app.schemas.common import ErrorResponse, StandardErrorWrapper
import asyncio
from sqlalchemy import text
from fastapi.responses import Response

# Optional monitoring libs (import lazily in endpoints)
_SENTRY_ENABLED = False
try:
    if getattr(settings, "SENTRY_DSN", None):
        import sentry_sdk  # type: ignore
        from sentry_sdk.integrations.asgi import SentryAsgiMiddleware  # type: ignore
        sentry_sdk.init(dsn=settings.SENTRY_DSN)
        _SENTRY_ENABLED = True
        get_logger("app.sentry").info("Sentry initialized")
except Exception:
    get_logger("app.sentry").exception("Failed to initialize Sentry; continuing without it")


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

# If Sentry was initialized, wrap the app so Sentry captures unhandled errors
if _SENTRY_ENABLED:
    try:
        # SentryAsgiMiddleware is a WSGI/ASGI middleware wrapper; wrap app instance
        from sentry_sdk.integrations.asgi import SentryAsgiMiddleware  # type: ignore
        app = SentryAsgiMiddleware(app)
        get_logger("app.sentry").info("Sentry ASGI middleware attached")
    except Exception:
        get_logger("app.sentry").exception("Failed to attach Sentry ASGI middleware")


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


# Helper to produce standardized JSON responses for errors
def _format_error_response(status: int, code: str, message: str, details=None):
    body = StandardErrorWrapper(
        success=False,
        error=ErrorResponse(status=status, code=code, message=message, details=details),
    )
    return JSONResponse(status_code=status, content=jsonable_encoder(body))


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Keep original detail if present, but map to our error model
    message = exc.detail if exc.detail is not None else "HTTP error"
    code = getattr(exc, "headers", {}).get("x-error-code") if isinstance(getattr(exc, "headers", None), dict) else str(exc.status_code)
    return _format_error_response(status=exc.status_code, code=str(code), message=str(message))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Return structured validation errors in `details`
    details = exc.errors()
    return _format_error_response(status=422, code="validation_error", message="Validation error", details=details)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log and return a generic 500 response without leaking internals
    get_logger("app.errors").exception("Unhandled exception: %s", exc)
    return _format_error_response(status=500, code="internal_server_error", message="Internal server error")


# Expose the new error schemas/components in the OpenAPI schema so clients can
# discover the standardized error format.
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(title=app.title, version=app.version, routes=app.routes, description=app.description)
    components = openapi_schema.setdefault("components", {})
    schemas = components.setdefault("schemas", {})
    # Add schemas using Pydantic model schema representations
    schemas["ErrorResponse"] = ErrorResponse.schema()
    schemas["StandardErrorWrapper"] = StandardErrorWrapper.schema()
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


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
    """Combined health endpoint returning liveness and readiness.

    - liveness: basic process-level check
    - readiness: DB connectivity check
    """
    # Liveness
    liveness = {"status": "alive"}

    # Readiness: check DB connectivity by running a simple SELECT 1
    async def _db_check():
        try:
            def _check():
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                return True
            ok = await asyncio.to_thread(_check)
            return {"database": "connected" if ok else "down", "ready": ok}
        except Exception:
            return {"database": "down", "ready": False}

    readiness = await _db_check()

    status = "healthy" if readiness.get("ready") else "unhealthy"
    code = 200 if readiness.get("ready") else 503
    # Keep top-level `database` key for backward compatibility with existing clients/tests
    top = {"status": status, "database": readiness.get("database"), "liveness": liveness, "readiness": readiness}
    return JSONResponse(status_code=code, content=top)


@app.get("/health/liveness")
async def liveness():
    return {"status": "alive"}


@app.get("/health/readiness")
async def readiness():
    try:
        def _check():
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        ok = await asyncio.to_thread(_check)
        if ok:
            return {"status": "ready", "database": "connected"}
        return JSONResponse(status_code=503, content={"status": "not_ready", "database": "down"})
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready", "database": "down"})


@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics. If `prometheus_client` isn't installed,
    return 501 Not Implemented so callers know metrics aren't available.
    """
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST  # type: ignore
    except Exception:
        return JSONResponse(status_code=501, content={"error": "prometheus-client not installed"})

    try:
        data = await asyncio.to_thread(generate_latest)
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)
    except Exception:
        get_logger("app.metrics").exception("Failed to generate metrics")
        return JSONResponse(status_code=500, content={"error": "failed to generate metrics"})


if __name__ == "__main__":
    import uvicorn
    # Run the app object directly to avoid import path issues when executing
    # this module as a script (ensures correct app is passed to Uvicorn).
    logger = get_logger("app.__main__")
    logger.info("Starting Uvicorn (host=%s port=%s reload=%s)", settings.HOST, settings.PORT, settings.RELOAD)
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
