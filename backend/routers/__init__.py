from backend.routers.system import router as system_router
from backend.routers.cameras import router as cameras_router
from backend.routers.vehicles import router as vehicles_router
from backend.routers.traffic import router as traffic_router
from backend.routers.blacklist import router as blacklist_router

__all__ = [
    "system_router",
    "cameras_router",
    "vehicles_router",
    "traffic_router",
    "blacklist_router",
]
