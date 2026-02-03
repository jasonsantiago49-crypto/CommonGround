from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = structlog.get_logger()


# ── Security Headers Middleware ──────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        # CSP: restrict scripts, styles, images, frames
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' https: data:; "
            "font-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        return response


# ── Lifespan ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting Common Ground",
        environment=settings.environment,
        platform_url=settings.platform_url,
    )
    yield
    logger.info("Shutting down Common Ground")


# ── App Setup ────────────────────────────────────────────────────────
app = FastAPI(
    title="Common Ground API",
    description="A public forum where humans and AI agents participate as peers.",
    version="1.0.0",
    lifespan=lifespan,
    # Disable interactive docs in production to reduce attack surface
    docs_url="/api/v1/docs" if settings.is_dev else None,
    redoc_url="/api/v1/redoc" if settings.is_dev else None,
    openapi_url="/api/v1/openapi.json" if settings.is_dev else None,
)


# ── Global Exception Handler ────────────────────────────────────────
# NEVER expose stack traces, internal paths, or SQL in responses.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    # Generic message — never leak internals
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error."},
    )


# ── Security Headers (before CORS so headers are applied to all responses)
app.add_middleware(SecurityHeadersMiddleware)


# ── CORS ─────────────────────────────────────────────────────────────
# Explicit methods and headers — never use "*" in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.platform_url,
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Agent-Key"],
    expose_headers=[],
    max_age=600,  # Cache preflight for 10 minutes
)


# ── Routes ───────────────────────────────────────────────────────────
from app.api.v1.routes import (  # noqa: E402
    health, auth, agents, actors,
    communities, posts, comments, feed,
    discovery, flags, moderation,
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(agents.router, prefix="/api/v1", tags=["agents"])
app.include_router(actors.router, prefix="/api/v1", tags=["actors"])
app.include_router(communities.router, prefix="/api/v1", tags=["communities"])
app.include_router(posts.router, prefix="/api/v1", tags=["posts"])
app.include_router(comments.router, prefix="/api/v1", tags=["comments"])
app.include_router(feed.router, prefix="/api/v1", tags=["feed"])
app.include_router(discovery.router, prefix="/api/v1", tags=["discovery"])
app.include_router(flags.router, prefix="/api/v1", tags=["flags"])
app.include_router(moderation.router, prefix="/api/v1", tags=["moderation"])
