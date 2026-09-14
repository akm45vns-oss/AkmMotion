from fastapi import APIRouter
from app.api.v1.endpoints import auth, projects, ai, scenes, render, settings, characters

api_router = APIRouter(prefix="/v1")

# Include Endpoints Routers
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(ai.router)
api_router.include_router(scenes.router)
api_router.include_router(render.router)
api_router.include_router(settings.router)
api_router.include_router(characters.router)


@api_router.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "AkmMotion API",
        "version": "6.2.0"
    }