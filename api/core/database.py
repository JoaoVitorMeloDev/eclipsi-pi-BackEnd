"""Conexão com PostgreSQL hospedado pelo Supabase."""

from __future__ import annotations

import psycopg2
from psycopg2.extensions import connection

from .config import database_config


def get_db() -> connection:
    """Abre uma nova conexão com o banco configurado no ambiente.

    O ciclo de vida da conexão é responsabilidade do endpoint que a abriu.
    As migrations são aplicadas manualmente no Supabase e nunca por esta API.
    """
    return psycopg2.connect(**database_config())
