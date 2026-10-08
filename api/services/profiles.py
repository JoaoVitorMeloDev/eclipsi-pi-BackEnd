"""Consultas reutilizáveis relacionadas a perfis e papéis de acesso."""

from __future__ import annotations

from typing import Any


def role_for_user(cursor: Any, user_id: str) -> str | None:
    cursor.execute("select role from public.profiles where id = %s", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else None


def is_admin(cursor: Any, user_id: str) -> bool:
    return role_for_user(cursor, user_id) == "admin"


def doctor_profile(cursor: Any, user_id: str) -> Any | None:
    cursor.execute(
        """select id, nome, especialidade, valor_hora
           from public.profiles where id = %s and role = 'medico'""",
        (user_id,),
    )
    return cursor.fetchone()
