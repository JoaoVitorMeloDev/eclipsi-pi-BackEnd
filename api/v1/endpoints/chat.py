from flask import Blueprint, jsonify, request, g
from api.core.database import get_db
from api.core.security import require_auth


bp = Blueprint('chat_v1', __name__, url_prefix='/api/v1/chat')


def participant(cur, conversation_id):
    cur.execute(
        'select id, paciente_id, medico_id from public.conversations where id = %s and (paciente_id = %s or medico_id = %s)',
        (str(conversation_id), g.auth_user_id, g.auth_user_id)
    )
    return cur.fetchone()


@bp.get('/conversations')
@require_auth
def conversations():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """select c.id, c.appointment_id, c.criado_em, p.nome, m.nome,
                      (select body from public.messages x where x.conversation_id = c.id order by x.criado_em desc limit 1),
                      (select max(criado_em) from public.messages x where x.conversation_id = c.id)
               from public.conversations c join public.profiles p on p.id = c.paciente_id join public.profiles m on m.id = c.medico_id
               where c.paciente_id = %s or c.medico_id = %s order by coalesce((select max(criado_em) from public.messages x where x.conversation_id = c.id), c.criado_em) desc""",
            (g.auth_user_id, g.auth_user_id)
        )

        data = [
            {
                'id': str(r[0]),
                'appointment_id': str(r[1]),
                'criado_em': r[2].isoformat(),
                'paciente_nome': r[3],
                'medico_nome': r[4],
                'ultima_mensagem': r[5],
                'ultima_mensagem_em': r[6].isoformat() if r[6] else None
            }
            for r in cur.fetchall()
        ]

        return jsonify({
            'success': True,
            'conversations': data
        })
    finally:
        conn.close()


@bp.post('/conversations')
@require_auth
def create_conversation():
    appointment_id = (request.get_json() or {}).get('appointment_id')

    if not appointment_id:
        return jsonify({
            'success': False,
            'message': 'Informe a consulta.'
        }), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            'select id, paciente_id, medico_id from public.appointments where id = %s and (paciente_id = %s or medico_id = %s)',
            (appointment_id, g.auth_user_id, g.auth_user_id)
        )

        appointment = cur.fetchone()

        if not appointment:
            return jsonify({
                'success': False,
                'message': 'Consulta não encontrada ou sem permissão.'
            }), 404

        cur.execute(
            'select id from public.conversations where appointment_id = %s',
            (appointment_id,)
        )
        existing = cur.fetchone()

        if existing:
            return jsonify({
                'success': True,
                'conversation_id': str(existing[0])
            })

        cur.execute(
            'insert into public.conversations (appointment_id, paciente_id, medico_id) values (%s, %s, %s) returning id',
            (appointment_id, appointment[1], appointment[2])
        )

        cid = cur.fetchone()[0]
        conn.commit()

        return jsonify({
            'success': True,
            'conversation_id': str(cid)
        }), 201
    finally:
        conn.close()


@bp.get('/conversations/<uuid:conversation_id>/messages')
@require_auth
def messages(conversation_id):
    conn = get_db()
    try:
        cur = conn.cursor()

        if not participant(cur, conversation_id):
            return jsonify({
                'success': False,
                'message': 'Conversa não encontrada ou sem permissão.'
            }), 404

        cur.execute(
            'select id, sender_id, body, criado_em, lida_em from public.messages where conversation_id = %s order by criado_em',
            (str(conversation_id),)
        )

        data = [
            {
                'id': str(r[0]),
                'sender_id': str(r[1]),
                'body': r[2],
                'criado_em': r[3].isoformat(),
                'lida_em': r[4].isoformat() if r[4] else None
            }
            for r in cur.fetchall()
        ]

        return jsonify({
            'success': True,
            'messages': data
        })
    finally:
        conn.close()


@bp.post('/conversations/<uuid:conversation_id>/messages')
@require_auth
def send_message(conversation_id):
    body = ((request.get_json() or {}).get('body') or '').strip()

    if not body or len(body) > 4000:
        return jsonify({
            'success': False,
            'message': 'Mensagem inválida.'
        }), 400

    conn = get_db()
    try:
        cur = conn.cursor()

        if not participant(cur, conversation_id):
            return jsonify({
                'success': False,
                'message': 'Conversa não encontrada ou sem permissão.'
            }), 404

        cur.execute(
            'insert into public.messages (conversation_id, sender_id, body) values (%s, %s, %s) returning id, criado_em',
            (str(conversation_id), g.auth_user_id, body)
        )

        row = cur.fetchone()
        conn.commit()

        return jsonify({
            'success': True,
            'message': {
                'id': str(row[0]),
                'sender_id': g.auth_user_id,
                'body': body,
                'criado_em': row[1].isoformat()
            }
        }), 201
    finally:
        conn.close()