"""Configurações centralizadas da API Flask."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(ENV_FILE)


def cors_origins() -> list[str]:
    """Retorna as origens permitidas pela API, sem itens vazios."""
    configured = os.getenv("CORS_ORIGINS", "*")
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


def database_config() -> dict[str, str | None]:
    """Dados de conexão PostgreSQL/Supabase lidos do ambiente."""
    return {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "postgres"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }
