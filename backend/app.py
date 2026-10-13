"""
backend/app.py

Unified FastAPI application for SIH 2026 Traffic Intelligence & Vehicle Journey System.
Plate-first architecture connecting 4 CCTV cameras across Junction A & Junction B.
Includes real traffic analytics, Haversine estimated speed, OD matrix,
Relative Congestion Index, Watchlist CRUD, Blacklist alerts, and vehicle journey tracking.

This file is a factory: it creates the FastAPI app, registers middleware, sets up
startup events, and includes domain routers from backend.routers/.
"""

from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import (
    system_router,
    cameras_router,
    vehicles_router,
    traffic_router,
    blacklist_router,
)


def create_app() -> FastAPI:
    """Application factory: create and configure the FastAPI application."""
    app = FastAPI(
        title="City-Wide Traffic Intelligence & Plate-Based Journey API",
        description=(
            "Production-grade traffic intelligence, multi-camera vehicle tracking, "
            "and surveillance investigation platform connecting Junction A and Junction B."
        ),
        version="3.5.2",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def on_startup():
        """Auto-initialize database tables and seed baseline data on fresh cloud deploy."""
        try:
            from backend.database.connection import engine, is_db_connected
            if is_db_connected() and engine:
                import backend.database.models
                from backend.database.connection import Base
                Base.metadata.create_all(bind=engine)
                from backend.database.connection import SessionLocal
                from backend.database.models import Camera
                session = SessionLocal()
                cam_count = session.query(Camera).count()
                session.close()
                if cam_count == 0:
                    print("[Startup] Fresh cloud database detected. Running automated seed migration...")
                    from scripts.migrate_json_to_sqlite import migrate
                    migrate()
        except Exception as e:
            print(f"[Startup] Database init notice: {e}")

    @app.get("/")
    def root():
        return {
            "status": "online",
            "service": "SIH 2026 City-Wide Traffic Intelligence API",
            "version": "3.5.2",
            "docs": "/docs",
            "endpoints": [
                "/api/health",
                "/api/system/health",
                "/api/cameras",
                "/api/vehicles",
                "/api/vehicles/search",
                "/api/analytics",
                "/api/analytics/od",
                "/api/analytics/congestion",
                "/api/analytics/speed",
                "/api/alerts",
                "/api/watchlist",
                "/api/blacklist",
                "/api/observations",
            ],
        }

    # Include domain routers
    app.include_router(system_router)
    app.include_router(cameras_router)
    app.include_router(vehicles_router)
    app.include_router(traffic_router)
    app.include_router(blacklist_router)

    return app


app = create_app()


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run(
        "backend.app:app",
        host=host,
        port=port,
        reload=False if os.environ.get("PORT") else True,
    )
