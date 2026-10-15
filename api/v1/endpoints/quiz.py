from flask import Blueprint, jsonify, request, g
from api.core.database import get_db
from api.core.security import require_auth


bp = Blueprint('quiz_v1', __name__, url_prefix='/api/v1/quiz')


@bp.get('/questions')
@require_auth
def questions():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "select id, ordem, enunciado, opcoes from public.quiz_questions where ativo = true order by ordem"
        )

        return jsonify({
            'success': True,
            'questions': [
                {
                    'id': r[0],
                    'ordem': r[1],
                    'enunciado': r[2],
                    'opcoes': r[3]
                }
                for r in cur.fetchall()
            ]
        })
    finally:
        conn.close()


@bp.post('/attempts')
@require_auth
def submit():
    answers = (request.get_json() or {}).get('answers')

    if not isinstance(answers, list) or not answers:
        return jsonify({
            'success': False,
            'message': 'Responda ao questionário.'
        }), 400

    normalized = {}

    try:
        for item in answers:
            question_id = int(item['question_id'])
            selected = int(item['resposta'])

            if question_id in normalized:
                return jsonify({
                    'success': False,
                    'message': 'Questão respondida mais de uma vez.'
                }), 400

            normalized[question_id] = selected

    except (KeyError, TypeError, ValueError):
        return jsonify({
            'success': False,
            'message': 'Respostas inválidas.'
        }), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            'select id, resposta_correta, jsonb_array_length(opcoes) from public.quiz_questions where ativo = true and id = any(%s)',
            (list(normalized.keys()),)
        )
        rows = cur.fetchall()

        if len(rows) != len(normalized):
            return jsonify({
                'success': False,
                'message': 'O questionário está incompleto ou contém questões inválidas.'
            }), 400

        score = 0

        for question_id, correct, option_count in rows:
            selected = normalized[question_id]

            if selected < 0 or selected >= option_count:
                return jsonify({
                    'success': False,
                    'message': 'Opção inválida.'
                }), 400

            if selected == correct:
                score += 1

        cur.execute(
            'insert into public.quiz_attempts (user_id, pontuacao, total) values (%s, %s, %s) returning id, concluido_em',
            (g.auth_user_id, score, len(rows))
        )

        attempt_id, completed = cur.fetchone()

        for question_id, correct, _ in rows:
            cur.execute(
                'insert into public.quiz_answers (attempt_id, question_id, resposta, correta) values (%s, %s, %s, %s)',
                (
                    attempt_id,
                    question_id,
                    normalized[question_id],
                    normalized[question_id] == correct
                )
            )

        conn.commit()

        return jsonify({
            'success': True,
            'result': {
                'id': str(attempt_id),
                'pontuacao': score,
                'total': len(rows),
                'percentual': round(score / len(rows) * 100),
                'concluido_em': completed.isoformat()
            }
        }), 201
    finally:
        conn.close()


@bp.get('/history')
@require_auth
def history():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            'select id, pontuacao, total, concluido_em from public.quiz_attempts where user_id = %s order by concluido_em desc',
            (g.auth_user_id,)
        )

        return jsonify({
            'success': True,
            'attempts': [
                {
                    'id': str(r[0]),
                    'pontuacao': r[1],
                    'total': r[2],
                    'percentual': round(r[1] / r[2] * 100) if r[2] else 0,
                    'concluido_em': r[3].isoformat()
                }
                for r in cur.fetchall()
            ]
        })
    finally:
        conn.close()