"""Contratos e valores permitidos usados pelos endpoints da API."""

from __future__ import annotations

USER_ROLES = frozenset({"paciente", "medico", "admin"})
APPOINTMENT_STATUSES = frozenset({"agendada", "realizada", "cancelada"})
PAYMENT_STATUSES = frozenset({"pago", "falhou", "estornado", "pendente"})
PROFILE_UPDATE_FIELDS = frozenset(
    {
        "nome",
        "telefone",
        "idade",
        "genero",
        "descricao",
        "especialidade",
        "registro",
        "uf",
        "valor_hora",
    }
)
