"""Conexão com PostgreSQL hospedado pelo Supabase."""

from __future__ import annotations

import psycopg2
from psycopg2.extensions import connection

from .config import database_config, database_url


def get_db() -> connection:
    dsn = database_url()
    if dsn:
        return psycopg2.connect(dsn, sslmode="require")
    return psycopg2.connect(**database_config())
