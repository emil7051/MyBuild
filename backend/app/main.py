"""FastAPI entrypoint for the TCO web platform backend."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api import api_router
from backend.app.core.config import settings
from backend.app.db.session import init_db


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        await init_db()
        yield

    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.backend_cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    frontend_dist = (
        Path(__file__).parent.parent.parent / "frontend" / "dist"
    ).resolve()
    if frontend_dist.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(frontend_dist / "assets")),
            name="assets",
        )

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            requested_path = (frontend_dist / full_path).resolve()
            if requested_path.is_relative_to(frontend_dist):
                if requested_path.is_file():
                    return FileResponse(requested_path)
            return FileResponse(frontend_dist / "index.html")

    else:

        @app.get("/", tags=["system"])
        def root() -> dict[str, str]:
            return {"message": "TCO Web Platform API", "version": settings.version}

    return app


app = create_app()
