# Backend EcliPsi

API do Projeto Integrador III ADS da Faculdade Senac PE, responsável pela plataforma de descoberta, comparação e agendamento em saúde mental.

- Site oficial: https://eclipsi.dev
- Implementação real deste repositório: Python, Flask, psycopg2 e PostgreSQL/Supabase
- Hospedagem: Render
- Frontend: Expo/React Native Web na Vercel
- Infraestrutura: Cloudflare

O workspace informado originalmente cita FastAPI, mas os arquivos reais deste repositório usam Flask. O contrato HTTP atual deve ser preservado.

## Segurança

- Cloudflare WAF e Rate Limiting
- CORS restrito por `CORS_ORIGINS`
- JWT Bearer via `JWT_SECRET`/`SUPABASE_JWT_SECRET`
- RBAC por cargo em `public.users`
- RLS e constraints no PostgreSQL/Supabase

## Execução local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

## Verificações

```bash
pytest -q
python check_database.py
python3 -m py_compile app.py api/**/*.py
```

