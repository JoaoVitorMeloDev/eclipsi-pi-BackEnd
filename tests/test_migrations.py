from pathlib import Path

ROOT = Path(__file__).parents[2]
MIGRATIONS = ROOT / 'database' / 'migrations'


def test_migrations_are_complete_and_ordered():
    expected = [
        '000_extensions.sql', '001_profiles_supabase_auth.sql',
        '002_secure_uuid_domain.sql', '003_payments.sql',
        '004_chat.sql', '005_quiz.sql', '006_hardening.sql'
    ]
    assert [p.name for p in sorted(MIGRATIONS.glob('*.sql'))] == expected


def test_security_objects_exist_in_migrations():
    content = '\n'.join(p.read_text() for p in sorted(MIGRATIONS.glob('*.sql')))
    for term in ('enable row level security', 'create policy', 'gen_random_uuid'):
        assert term in content.lower()
