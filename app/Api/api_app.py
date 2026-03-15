from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.Api.db.sqlite_db import init_db
from app.Api.routers import administration, chat, datalake, executions, health, ingest, model_build, workflows


def create_api_app() -> FastAPI:
    app = FastAPI(
        title="InfoHub API",
        version="0.1.0",
        description="Backend API for InfoHub portal modules: ingest, chat, model build, and administration.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(workflows.router, prefix="/api/v1")
    app.include_router(ingest.router, prefix="/api/v1")
    app.include_router(executions.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(model_build.router, prefix="/api/v1")
    app.include_router(administration.router, prefix="/api/v1")
    app.include_router(datalake.router, prefix="/api/v1")

    return app


app = create_api_app()

