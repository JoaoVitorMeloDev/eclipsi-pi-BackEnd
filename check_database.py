from api.core.database import get_db

TABLES = ('profiles', 'appointments', 'payments', 'reviews', 'conversations', 'messages', 'quiz_questions', 'quiz_attempts', 'quiz_answers')

if __name__ == '__main__':
    conn = get_db()
    try:
        cur = conn.cursor()
        missing = []
        for table in TABLES:
            cur.execute('select to_regclass(%s)', (f'public.{table}',))
            if cur.fetchone()[0] is None:
                missing.append(table)
        if missing:
            raise SystemExit('Tabelas ausentes: ' + ', '.join(missing))
        print('Banco EcliPsi conectado e todas as tabelas principais foram encontradas.')
    finally:
        conn.close()
