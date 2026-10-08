from flask import Blueprint, jsonify, g
from api.core.database import get_db
from api.core.security import require_auth
from api.services.profiles import doctor_profile

bp = Blueprint('doctor_v1', __name__, url_prefix='/api/v1/doctor')

@bp.get('/dashboard')
@require_auth
def dashboard():
    conn = get_db()
    try:
        cur = conn.cursor(); doctor = doctor_profile(cur, g.auth_user_id)
        if not doctor: return jsonify({'success': False, 'message': 'Acesso restrito a profissionais.'}), 403
        cur.execute("select count(*) filter (where status = 'agendada'), count(*) filter (where status = 'realizada'), count(*) filter (where status = 'cancelada') from public.appointments where medico_id = %s", (g.auth_user_id,))
        scheduled, completed, canceled = cur.fetchone()
        cur.execute("select coalesce(sum(valor), 0), count(*) from public.appointments where medico_id = %s and status = 'realizada'", (g.auth_user_id,))
        total, count = cur.fetchone()
        cur.execute("select coalesce(round(avg(nota), 1), 0), count(*) from public.reviews where medico_id = %s", (g.auth_user_id,))
        rating, ratings = cur.fetchone()
        return jsonify({'success': True, 'doctor': {'id': str(doctor[0]), 'nome': doctor[1], 'especialidade': doctor[2], 'valor_hora': float(doctor[3]) if doctor[3] is not None else 0}, 'stats': {'agendadas': scheduled, 'realizadas': completed, 'canceladas': canceled, 'faturamento': float(total), 'consultas_pagantes': count, 'nota_media': float(rating), 'total_avaliacoes': ratings}})
    finally: conn.close()

@bp.get('/appointments')
@require_auth
def appointments():
    conn = get_db()
    try:
        cur = conn.cursor(); doctor = doctor_profile(cur, g.auth_user_id)
        if not doctor: return jsonify({'success': False, 'message': 'Acesso restrito a profissionais.'}), 403
        cur.execute("""select a.id, a.data_hora, a.valor, a.status, a.anotacoes, p.id, p.nome, p.email, p.telefone
                       from public.appointments a join public.profiles p on p.id = a.paciente_id
                       where a.medico_id = %s order by a.data_hora""", (g.auth_user_id,))
        data = [{'id': str(r[0]), 'data_hora': r[1].isoformat(), 'valor': float(r[2]), 'status': r[3], 'anotacoes': r[4], 'paciente_id': str(r[5]), 'paciente_nome': r[6], 'paciente_email': r[7], 'paciente_telefone': r[8]} for r in cur.fetchall()]
        return jsonify({'success': True, 'appointments': data})
    finally: conn.close()

@bp.get('/earnings')
@require_auth
def earnings():
    conn = get_db()
    try:
        cur = conn.cursor(); doctor = doctor_profile(cur, g.auth_user_id)
        if not doctor: return jsonify({'success': False, 'message': 'Acesso restrito a profissionais.'}), 403
        cur.execute("select coalesce(sum(valor), 0), count(*) from public.appointments where medico_id = %s and status = 'realizada'", (g.auth_user_id,))
        total, count = cur.fetchone()
        return jsonify({'success': True, 'total': float(total), 'consultas_realizadas': count, 'valor_hora': float(doctor[3]) if doctor[3] is not None else 0})
    finally: conn.close()
