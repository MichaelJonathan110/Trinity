"""TRINITY API entrypoint. OpenAPI docs are served at /docs (spec 51)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()

def create_app() -> FastAPI:
    app = FastAPI(
        title="TRINITY API",
        version="0.1.0",
        description="Fuel. Recover. Perform. Athlete performance platform API.",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(api_router, prefix=settings.API_V1)

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}

    return app


app = create_app()
