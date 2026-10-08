from flask import Blueprint, jsonify, request, g
from api.core.database import get_db
from api.core.security import require_auth

bp = Blueprint('reviews_v1', __name__, url_prefix='/api/v1/reviews')

@bp.post('')
@require_auth
def create_review():
    data = request.get_json() or {}
    appointment_id = data.get('appointment_id')
    try: rating = int(data.get('nota'))
    except (TypeError, ValueError): return jsonify({'success': False, 'message': 'Nota inválida.'}), 400
    comment = (data.get('comentario') or '').strip()[:500] or None
    if not appointment_id or rating < 1 or rating > 5: return jsonify({'success': False, 'message': 'Informe uma nota de 1 a 5.'}), 400
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""select id, medico_id from public.appointments where id = %s and paciente_id = %s and status = 'realizada'""", (appointment_id, g.auth_user_id))
        appointment = cur.fetchone()
        if not appointment: return jsonify({'success': False, 'message': 'Somente consultas realizadas suas podem ser avaliadas.'}), 400
        cur.execute('insert into public.reviews (appointment_id, medico_id, paciente_id, nota, comentario) values (%s, %s, %s, %s, %s) returning id', (appointment_id, appointment[1], g.auth_user_id, rating, comment))
        review_id = cur.fetchone()[0]; conn.commit(); return jsonify({'success': True, 'review_id': str(review_id)}), 201
    except Exception as exc:
        conn.rollback()
        if 'duplicate key' in str(exc).lower(): return jsonify({'success': False, 'message': 'Esta consulta já foi avaliada.'}), 409
        return jsonify({'success': False, 'message': 'Não foi possível registrar a avaliação.'}), 500
    finally: conn.close()

@bp.get('/doctor/<uuid:doctor_id>')
@require_auth
def doctor_reviews(doctor_id):
    conn = get_db()
    try:
        cur = conn.cursor(); cur.execute('select coalesce(round(avg(nota), 1), 0), count(*) from public.reviews where medico_id = %s', (str(doctor_id),)); average, total = cur.fetchone()
        cur.execute("""select r.id, r.nota, r.comentario, r.criado_em, p.nome
                       from public.reviews r join public.profiles p on p.id = r.paciente_id
                       where r.medico_id = %s order by r.criado_em desc limit 50""", (str(doctor_id),))
        data = [{'id': str(r[0]), 'nota': r[1], 'comentario': r[2], 'criado_em': r[3].isoformat(), 'paciente_nome': r[4]} for r in cur.fetchall()]
        return jsonify({'success': True, 'summary': {'media': float(average), 'total': total}, 'reviews': data})
    finally: conn.close()
