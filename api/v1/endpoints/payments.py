from decimal import Decimal

from flask import Blueprint, jsonify, request, g
from api.core.database import get_db
from api.core.security import require_auth
from api.schemas.domain import PAYMENT_STATUSES
from api.services.profiles import role_for_user


bp = Blueprint('payments_v1', __name__, url_prefix='/api/v1/payments')

FEE = Decimal('0.10')


@bp.post('')
@require_auth
def create_payment():
    data = request.get_json() or {}
    appointment_id = data.get('appointment_id')

    if not appointment_id:
        return jsonify({
            'success': False,
            'message': 'Informe a consulta.'
        }), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """select a.id, a.paciente_id, a.medico_id, a.valor, a.status
               from public.appointments a
               where a.id = %s and a.paciente_id = %s""",
            (appointment_id, g.auth_user_id)
        )

        appointment = cur.fetchone()

        if not appointment:
            return jsonify({
                'success': False,
                'message': 'Consulta não encontrada ou sem permissão.'
            }), 404

        if appointment[4] == 'cancelada':
            return jsonify({
                'success': False,
                'message': 'Consultas canceladas não podem ser pagas.'
            }), 400

        cur.execute(
            'select id, status, valor, taxa_plataforma, repasse from public.payments where appointment_id = %s',
            (appointment_id,)
        )
        existing = cur.fetchone()

        if existing:
            return jsonify({
                'success': True,
                'payment': {
                    'id': str(existing[0]),
                    'status': existing[1],
                    'valor': float(existing[2]),
                    'taxa_plataforma': float(existing[3]),
                    'repasse': float(existing[4])
                }
            })

        value = Decimal(str(appointment[3] or 0))
        fee = (value * FEE).quantize(Decimal('0.01'))
        payout = value - fee

        cur.execute(
            """insert into public.payments (appointment_id, paciente_id, medico_id, valor, taxa_plataforma, repasse, provedor)
               values (%s, %s, %s, %s, %s, %s, 'manual') returning id, status""",
            (
                appointment_id,
                appointment[1],
                appointment[2],
                value,
                fee,
                payout
            )
        )

        row = cur.fetchone()
        conn.commit()

        return jsonify({
            'success': True,
            'payment': {
                'id': str(row[0]),
                'status': row[1],
                'valor': float(value),
                'taxa_plataforma': float(fee),
                'repasse': float(payout)
            }
        }), 201
    finally:
        conn.close()


@bp.get('')
@require_auth
def list_payments():
    conn = get_db()
    try:
        cur = conn.cursor()
        current_role = role_for_user(cur, g.auth_user_id)

        if current_role == 'admin':
            cur.execute(
                """select p.id, p.appointment_id, p.valor, p.taxa_plataforma, p.repasse, p.status, p.criado_em, pa.nome, m.nome
                   from public.payments p
                   join public.profiles pa on pa.id = p.paciente_id
                   join public.profiles m on m.id = p.medico_id
                   order by p.criado_em desc"""
            )

        elif current_role == 'medico':
            cur.execute(
                """select p.id, p.appointment_id, p.valor, p.taxa_plataforma, p.repasse, p.status, p.criado_em, pa.nome, m.nome
                   from public.payments p
                   join public.profiles pa on pa.id = p.paciente_id
                   join public.profiles m on m.id = p.medico_id
                   where p.medico_id = %s
                   order by p.criado_em desc""",
                (g.auth_user_id,)
            )

        else:
            cur.execute(
                """select p.id, p.appointment_id, p.valor, p.taxa_plataforma, p.repasse, p.status, p.criado_em, pa.nome, m.nome
                   from public.payments p
                   join public.profiles pa on pa.id = p.paciente_id
                   join public.profiles m on m.id = p.medico_id
                   where p.paciente_id = %s
                   order by p.criado_em desc""",
                (g.auth_user_id,)
            )

        payments = [
            {
                'id': str(r[0]),
                'appointment_id': str(r[1]),
                'valor': float(r[2]),
                'taxa_plataforma': float(r[3]),
                'repasse': float(r[4]),
                'status': r[5],
                'criado_em': r[6].isoformat(),
                'paciente_nome': r[7],
                'medico_nome': r[8]
            }
            for r in cur.fetchall()
        ]

        return jsonify({
            'success': True,
            'payments': payments
        })
    finally:
        conn.close()


@bp.patch('/<uuid:payment_id>')
@require_auth
def update_payment(payment_id):
    data = request.get_json() or {}
    new_status = data.get('status')

    if new_status not in PAYMENT_STATUSES:
        return jsonify({
            'success': False,
            'message': 'Status inválido.'
        }), 400

    conn = get_db()
    try:
        cur = conn.cursor()

        if role_for_user(cur, g.auth_user_id) != 'admin':
            return jsonify({
                'success': False,
                'message': 'Somente administradores podem atualizar pagamentos.'
            }), 403

        cur.execute(
            'update public.payments set status = %s, atualizado_em = now() where id = %s returning id',
            (new_status, str(payment_id))
        )

        if not cur.fetchone():
            conn.rollback()
            return jsonify({
                'success': False,
                'message': 'Pagamento não encontrado.'
            }), 404

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Pagamento atualizado.'
        })
    finally:
        conn.close()