from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.database import async_session_factory

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic liveness check."""
    return {
        "status": "ok",
        "platform": settings.platform_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check - verifies DB connectivity."""
    checks = {"database": "unknown"}

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    all_ok = all(v == "connected" for v in checks.values())

    return {
        "status": "ok" if all_ok else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }
