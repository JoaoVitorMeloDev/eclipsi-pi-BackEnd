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
            "select role, count(*) from public.users group by role"
        )
        roles = {r[0]: r[1] for r in cur.fetchall()}

        cur.execute(
            "select count(*) from public.consultas"
        )
        appointments = cur.fetchone()[0]

        cur.execute(
            "select count(*) from public.consultas where status in ('concluida', 'realizada')"
        )
        completed = cur.fetchone()[0]

        cur.execute(
            """select coalesce(especialidade, 'Não informado'), count(*)
               from public.users
               where role in ('medico', 'profissional')
               group by coalesce(especialidade, 'Não informado')
               order by count(*) desc"""
        )
        especialidades = {row[0]: row[1] for row in cur.fetchall()}

        cur.execute(
            """select coalesce(sum(valor), 0),
                      coalesce(sum(taxa_plataforma), 0),
                      coalesce(sum(repasse), 0)
               from public.pagamentos"""
        )
        payment_totals = cur.fetchone()

        return jsonify({
            'success': True,
            'stats': {
                'pacientes': roles.get('paciente', 0),
                'medicos': roles.get('medico', 0) + roles.get('profissional', 0),
                'admins': roles.get('admin', 0),
                'consultas': appointments,
                'realizadas': completed,
                'especialidades': especialidades,
                'pagamentos': {
                    'valor': float(payment_totals[0]),
                    'taxa_plataforma': float(payment_totals[1]),
                    'repasse': float(payment_totals[2])
                }
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
            "select id, nome, telefone, role, especialidade, registro, created_at from public.users order by created_at desc"
        )

        data = [
            {
                'id': str(r[0]),
                'nome': r[1],
                'telefone': r[2],
                'role': r[3],
                'especialidade': r[4],
                'registro': r[5],
                'criado_em': r[6].isoformat() if r[6] else None
            }
            for r in cur.fetchall()
        ]

        return jsonify({
            'success': True,
            'users': data
        })
    finally:
        conn.close()


@bp.patch('/users/<int:user_id>')
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
            'update public.users set role = %s where id = %s returning id',
            (role, user_id)
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


@bp.delete('/users/<int:user_id>')
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

        if user_id == int(g.auth_user_id):
            return jsonify({
                'success': False,
                'message': 'O administrador não pode excluir a própria conta.'
            }), 400

        cur.execute(
            'delete from public.users where id = %s returning id',
            (user_id,)
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