from pathlib import Path

ROOT = Path(__file__).parents[1]
MIGRATIONS = ROOT / 'database' / 'migrations'


def test_migrations_are_complete_and_ordered():
    expected = [
        '000_extensions.sql', '001_profiles_supabase_auth.sql',
        '002_secure_uuid_domain.sql', '003_payments.sql',
        '004_chat.sql', '005_quiz.sql', '006_hardening.sql'
    ]
    assert [p.name for p in sorted(MIGRATIONS.glob('*.sql'))] == expected


def test_hardening_migration_protects_real_appointment_table():
    content = '\n'.join(p.read_text() for p in sorted(MIGRATIONS.glob('*.sql')))
    normalized = content.lower()
    assert 'ux_appointments_doctor_time' in normalized
    assert 'public.consultas' in normalized
    assert 'medico_id' in normalized
    assert 'data_hora' in normalized
    assert 'cancelada' in normalized
