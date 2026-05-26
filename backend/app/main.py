from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.version)
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_headers=["*"],
        allow_methods=["*"],
        allow_origins=list(settings.cors_origins),
    )
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
