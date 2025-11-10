"""FastAPI entrypoint for the TCO web platform backend."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import api_router
from backend.app.core.config import settings
from backend.app.db.session import init_db


def create_app() -> FastAPI:
    app = FastAPI(title=settings.project_name, version=settings.version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.on_event("startup")
    async def _startup() -> None:  # pragma: no cover - integration hook
        await init_db()

    @app.get("/", tags=["system"])
    def root() -> dict[str, str]:
        return {"message": "TCO Web Platform API", "version": settings.version}

    return app


app = create_app()
