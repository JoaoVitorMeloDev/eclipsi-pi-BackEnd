from flask import Blueprint, jsonify, request, g
from api.core.database import get_db
from api.core.security import require_auth
from api.schemas.domain import USER_ROLES
from api.services.profiles import is_admin


bp = Blueprint('admin_v1', __name__, url_prefix='/api/v1/admin')


@bp.get('/stats')
@require_auth
def stats():
    conn = get_db()
    try:
        cur = conn.cursor()

        if not is_admin(cur, g.auth_user_id):
            return jsonify({
                'success': False,
                'message': 'Acesso restrito ao administrador.'
            }), 403

        cur.execute(
            "select role, count(*) from public.profiles group by role"
        )
        roles = {r[0]: r[1] for r in cur.fetchall()}

        cur.execute(
            "select count(*) from public.appointments"
        )
        appointments = cur.fetchone()[0]

        cur.execute(
            "select count(*) from public.appointments where status = 'realizada'"
        )
        completed = cur.fetchone()[0]

        return jsonify({
            'success': True,
            'stats': {
                'pacientes': roles.get('paciente', 0),
                'medicos': roles.get('medico', 0),
                'admins': roles.get('admin', 0),
                'consultas': appointments,
                'realizadas': completed
            }
        })
    finally:
        conn.close()


@bp.get('/users')
@require_auth
def users():
    conn = get_db()
    try:
        cur = conn.cursor()

        if not is_admin(cur, g.auth_user_id):
            return jsonify({
                'success': False,
                'message': 'Acesso restrito ao administrador.'
            }), 403

        cur.execute(
            "select id, nome, telefone, role, especialidade, registro, criado_em from public.profiles order by criado_em desc"
        )

        data = [
            {
                'id': str(r[0]),
                'nome': r[1],
                'telefone': r[2],
                'role': r[3],
                'especialidade': r[4],
                'registro': r[5],
                'criado_em': r[6].isoformat()
            }
            for r in cur.fetchall()
        ]

        return jsonify({
            'success': True,
            'users': data
        })
    finally:
        conn.close()


@bp.patch('/users/<uuid:user_id>')
@require_auth
def update_user(user_id):
    data = request.get_json() or {}
    role = data.get('role')

    if role not in USER_ROLES:
        return jsonify({
            'success': False,
            'message': 'Role inválida.'
        }), 400

    conn = get_db()
    try:
        cur = conn.cursor()

        if not is_admin(cur, g.auth_user_id):
            return jsonify({
                'success': False,
                'message': 'Acesso restrito ao administrador.'
            }), 403

        cur.execute(
            'update public.profiles set role = %s where id = %s returning id',
            (role, str(user_id))
        )

        if not cur.fetchone():
            conn.rollback()
            return jsonify({
                'success': False,
                'message': 'Usuário não encontrado.'
            }), 404

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Usuário atualizado.'
        })
    finally:
        conn.close()


@bp.delete('/users/<uuid:user_id>')
@require_auth
def delete_user(user_id):
    conn = get_db()
    try:
        cur = conn.cursor()

        if not is_admin(cur, g.auth_user_id):
            return jsonify({
                'success': False,
                'message': 'Acesso restrito ao administrador.'
            }), 403

        if str(user_id) == g.auth_user_id:
            return jsonify({
                'success': False,
                'message': 'O administrador não pode excluir a própria conta.'
            }), 400

        cur.execute(
            'delete from public.profiles where id = %s returning id',
            (str(user_id),)
        )

        if not cur.fetchone():
            conn.rollback()
            return jsonify({
                'success': False,
                'message': 'Usuário não encontrado.'
            }), 404

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Perfil excluído.'
        })
    finally:
        conn.close()