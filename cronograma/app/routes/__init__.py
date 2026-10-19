"""Pacote de rotas do Cronograma."""

from routes.auth import router as auth_router
from routes.areas import router as areas_router
from routes.tasks import router as tasks_router
from routes.sessoes import router as sessoes_router
from routes.gamification import router as gamification_router
from routes.stats import router as stats_router
from routes.missions import router as missions_router
from routes.admin import router as admin_router

__all__ = [
    "auth_router",
    "areas_router",
    "tasks_router",
    "sessoes_router",
    "gamification_router",
    "stats_router",
    "missions_router",
    "admin_router",
]
