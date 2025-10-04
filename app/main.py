from fastapi import FastAPI

from app.routers import health
from app.routers import stations as stations_router
from app.routers import ingestion as ingestion_router
from app.routers import query as query_router
from app.routers import forecast as forecast_router
from app.routers import source as source_router
from app.routers import policy as policy_router
from app.db.session import Base, engine


def create_app() -> FastAPI:
    app = FastAPI(title="Delhi-NCR AI Pollution Backend", version="0.1.0")

    # Routers
    app.include_router(health.router, prefix="/api")
    app.include_router(stations_router.router, prefix="/api")
    app.include_router(ingestion_router.router, prefix="/api")
    app.include_router(query_router.router, prefix="/api")
    app.include_router(forecast_router.router, prefix="/api")
    app.include_router(source_router.router, prefix="/api")
    app.include_router(policy_router.router, prefix="/api")

    @app.on_event("startup")
    def _startup_create_tables():
        # Ensure DB tables exist
        Base.metadata.create_all(bind=engine)

    return app


app = create_app()
