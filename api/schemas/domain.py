"""Contratos e valores permitidos usados pelos endpoints da API."""

from __future__ import annotations

USER_ROLES = frozenset({"paciente", "profissional", "medico", "admin"})
APPOINTMENT_STATUSES = frozenset({"agendada", "concluida", "realizada", "cancelada"})
PAYMENT_STATUSES = frozenset({"pago", "falhou", "estornado", "pendente"})
PROFILE_UPDATE_FIELDS = frozenset(
    {
        "nome",
        "foto",
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
