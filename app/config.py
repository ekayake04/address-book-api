"""Application settings, overridable through environment variables."""

import os

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./addresses.db")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
