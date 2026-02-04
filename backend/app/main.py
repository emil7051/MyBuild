"""FastAPI entrypoint for the TCO web platform backend.

SEC-004: Request body size limits via middleware.
SEC-008: Rate limiting via slowapi.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

try:
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
except ModuleNotFoundError:  # pragma: no cover - optional dependency at runtime
    _rate_limit_exceeded_handler = None
    RateLimitExceeded = None

from backend.app.api import api_router
from backend.app.api.router import limiter
from backend.app.core.config import settings
from backend.app.core.middleware import RequestSizeLimitMiddleware
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

    # Add rate limiter state (SEC-008)
    if _rate_limit_exceeded_handler and RateLimitExceeded:
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add request size limit middleware (SEC-004)
    app.add_middleware(RequestSizeLimitMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.backend_cors_origins],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
        allow_headers=["Content-Type", "X-Analytics-Key"],
    )

    app.include_router(api_router)

    frontend_dist = (
        Path(__file__).parent.parent.parent / "frontend" / "dist"
    ).resolve()
    if frontend_dist.exists():
        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            app.mount(
                "/assets",
                StaticFiles(directory=str(assets_dir)),
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
