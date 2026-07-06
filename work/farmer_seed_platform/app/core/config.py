from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    DATABASE_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "seed_platform.db"))
    TEMPLATES_DIR = BASE_DIR / "templates"
    STATIC_DIR = BASE_DIR / "static"
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
