"""Conexão com PostgreSQL hospedado pelo Supabase."""

from __future__ import annotations

import psycopg2
from psycopg2.extensions import connection

from .config import database_config


def get_db() -> connection:
    return psycopg2.connect(**database_config())
