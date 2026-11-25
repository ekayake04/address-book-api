"""FastAPI application entry point."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.logging_config import setup_logging
from app.routers import addresses

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database ready at %s", engine.url)
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Address Book API",
    description="Create, update, delete and search addresses by distance.",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(addresses.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Simple liveness check."""
    return {"status": "ok"}
