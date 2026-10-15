from datetime import datetime, timezone
from uuid import UUID

from flask import Blueprint, g, jsonify, request
from api.core.database import get_db
from api.core.security import require_auth
from api.schemas.domain import APPOINTMENT_STATUSES, PROFILE_UPDATE_FIELDS


bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


def _profile_role(cur, user_id):
    cur.execute(
        "select id, nome, email, role from public.profiles where id = %s",
        (user_id,)
    )
    return cur.fetchone()


def _doctor(row):
    return {
        "id": str(row[0]),
        "nome": row[1],
        "especialidade": row[2],
        "registro": row[3],
        "uf": row[4],
        "descricao": row[5],
        "valor_hora": float(row[6]) if row[6] is not None else None
    }


@bp.get("/profile/me")
@require_auth
def my_profile():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """select id, nome, telefone, role, idade, genero, especialidade, registro, uf, descricao, valor_hora
               from public.profiles where id = %s""",
            (g.auth_user_id,)
        )

        row = cur.fetchone()

        if not row:
            return jsonify({
                "success": False,
                "message": "Perfil não encontrado."
            }), 404

        return jsonify({
            "success": True,
            "profile": {
                "id": str(row[0]),
                "nome": row[1],
                "telefone": row[2],
                "role": row[3],
                "idade": row[4],
                "genero": row[5],
                "especialidade": row[6],
                "registro": row[7],
                "uf": row[8],
                "descricao": row[9],
                "valor_hora": float(row[10]) if row[10] is not None else None
            }
        })
    finally:
        conn.close()


@bp.patch("/profile/me")
@require_auth
def update_my_profile():
    data = request.get_json() or {}

    values = {
        key: data[key]
        for key in PROFILE_UPDATE_FIELDS
        if key in data
    }

    if "nome" in values and (
        not isinstance(values["nome"], str)
        or not values["nome"].strip()
    ):
        return jsonify({
            "success": False,
            "message": "Nome inválido."
        }), 400

    if not values:
        return jsonify({
            "success": False,
            "message": "Nenhum campo para atualizar."
        }), 400

    conn = get_db()
    try:
        cur = conn.cursor()

        sets = ", ".join(
            f"{key} = %s"
            for key in values
        )

        cur.execute(
            f"update public.profiles set {sets} where id = %s returning id",
            (*values.values(), g.auth_user_id)
        )

        if not cur.fetchone():
            conn.rollback()
            return jsonify({
                "success": False,
                "message": "Perfil não encontrado."
            }), 404

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Perfil atualizado."
        })
    finally:
        conn.close()


@bp.get("/doctors")
@require_auth
def doctors():
    q = (request.args.get("q") or "").strip()[:100]

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """select id, nome, especialidade, registro, uf, descricao, valor_hora
               from public.profiles
               where role = 'medico' and (%s = '' or nome ilike %s or coalesce(especialidade,'') ilike %s or coalesce(descricao,'') ilike %s)
               order by nome""",
            (q, f"%{q}%", f"%{q}%", f"%{q}%")
        )

        return jsonify({
            "success": True,
            "doctors": [
                _doctor(r)
                for r in cur.fetchall()
            ]
        })
    finally:
        conn.close()


@bp.post("/appointments")
@require_auth
def create_appointment():
    data = request.get_json() or {}

    try:
        doctor_id = UUID(str(data["medico_id"]))
        when = datetime.fromisoformat(
            str(data["data_hora"]).replace("Z", "+00:00")
        )
    except (KeyError, ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Médico ou data inválidos."
        }), 400

    if when.tzinfo is None:
        return jsonify({
            "success": False,
            "message": "A data deve conter fuso horário."
        }), 400

    if when <= datetime.now(timezone.utc):
        return jsonify({
            "success": False,
            "message": "Escolha uma data futura."
        }), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        profile = _profile_role(cur, g.auth_user_id)

        if not profile or profile[3] != "paciente":
            return jsonify({
                "success": False,
                "message": "Somente pacientes podem agendar consultas."
            }), 403

        cur.execute(
            "select id, valor_hora from public.profiles where id = %s and role = 'medico'",
            (str(doctor_id),)
        )
        doctor = cur.fetchone()

        if not doctor:
            return jsonify({
                "success": False,
                "message": "Profissional não encontrado."
            }), 404

        cur.execute(
            """insert into public.appointments (paciente_id, medico_id, data_hora, valor)
               values (%s, %s, %s, %s) returning id, data_hora, valor, status""",
            (g.auth_user_id, str(doctor_id), when, doctor[1] or 0)
        )

        row = cur.fetchone()
        conn.commit()

        return jsonify({
            "success": True,
            "appointment": {
                "id": str(row[0]),
                "data_hora": row[1].isoformat(),
                "valor": float(row[2]),
                "status": row[3]
            }
        }), 201

    except Exception as exc:
        conn.rollback()

        if (
            "ux_appointments_doctor_time" in str(exc)
            or "duplicate key" in str(exc).lower()
        ):
            return jsonify({
                "success": False,
                "message": "Este horário já está ocupado."
            }), 409

        return jsonify({
            "success": False,
            "message": "Não foi possível criar a consulta."
        }), 500

    finally:
        conn.close()


@bp.get("/appointments")
@require_auth
def list_appointments():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """select a.id, a.data_hora, a.valor, a.status, a.anotacoes,
                      p.id, p.nome, d.id, d.nome, d.especialidade
               from public.appointments a
               join public.profiles p on p.id = a.paciente_id
               join public.profiles d on d.id = a.medico_id
               where a.paciente_id = %s or a.medico_id = %s
               order by a.data_hora""",
            (g.auth_user_id, g.auth_user_id)
        )

        items = [
            {
                "id": str(r[0]),
                "data_hora": r[1].isoformat(),
                "valor": float(r[2]),
                "status": r[3],
                "anotacoes": r[4],
                "paciente_id": str(r[5]),
                "paciente_nome": r[6],
                "medico_id": str(r[7]),
                "medico_nome": r[8],
                "especialidade": r[9]
            }
            for r in cur.fetchall()
        ]

        return jsonify({
            "success": True,
            "appointments": items
        })
    finally:
        conn.close()


@bp.patch("/appointments/<uuid:appointment_id>")
@require_auth
def update_appointment(appointment_id):
    data = request.get_json() or {}
    status = data.get("status")

    if status not in APPOINTMENT_STATUSES:
        return jsonify({
            "success": False,
            "message": "Status inválido."
        }), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """update public.appointments set status = %s
               where id = %s and (paciente_id = %s or medico_id = %s) returning id""",
            (status, str(appointment_id), g.auth_user_id, g.auth_user_id)
        )

        if not cur.fetchone():
            conn.rollback()
            return jsonify({
                "success": False,
                "message": "Consulta não encontrada ou sem permissão."
            }), 404

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Consulta atualizada."
        })
    finally:
        conn.close()