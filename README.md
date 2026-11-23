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
- CORS restrito a `https://eclipsi.dev`, `https://www.eclipsi.dev` e `http://localhost:8081`
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


## Disponibilidade, triagem e PIX

Aplique `supabase/migrations/20261124_full_mvp.sql` no Supabase antes de
publicar a API. A migração parte das tabelas legadas `users` e `consultas`
com IDs inteiros. Ela mantém os IDs e contratos existentes. Valide primeiro
numa cópia do banco, especialmente os tipos, defaults e constraints da tabela
`pagamentos` existente e a ausência de agendamentos ativos duplicados. A
conexão do Flask deve usar o papel de backend autorizado a acessar as tabelas
sob RLS. A aplicação verifica identidade, perfil e ownership em cada operação.

- Consulte a grade autenticada em `GET /api/v1/professionals/{id}/availability`.
  Profissionais gerenciam seus próprios slots em `POST /api/v1/professional/availability`
  com `data_hora` ISO 8601 e fuso, e em `DELETE /api/v1/professional/availability/{slot_id}`.
- `POST /api/v1/patient/appointments` aceita `slot_id` ou
  `medico_id` e `data_hora`. O banco impede duas consultas ativas no mesmo
  horário. `POST /api/v1/appointments` preserva o agendamento com o payload
  antigo para o frontend atual e também valida a grade quando recebe `slot_id`.
- `POST /api/v1/patient/triage` grava a triagem da conta autenticada.
  `GET /api/v1/patient/doctors` e `/api/v1/patient/doctors/recommended`
  retornam recomendações ordenadas pelo score. O score pondera especialidade
  (35), abordagem (25), modalidade (15), orçamento (20) e disponibilidade
  para urgência nas próximas 48 horas (5).
- Defina `MERCADO_PAGO_ACCESS_TOKEN` no ambiente do Render para cobrança
  real. Configure no Mercado Pago o webhook de pagamentos em
  `/api/v1/payments/webhook/mercadopago`. O backend confere o pagamento
  com o provedor antes de registrar a aprovação. Com a variável vazia,
  o BR Code de demonstração usa um domínio reservado sem cobrança bancária,
  e a confirmação manual funciona exclusivamente para registros desse modo.
- Para gerar os seis perfis fictícios e slots dos próximos sete dias,
  configure `DATABASE_URL` para um banco de demonstração e execute
  `python scripts/seed_demo.py --demo`. Os perfis não possuem senha utilizável.
  No SQL Editor de um ambiente de demonstração, acrescente
  `set local eclipsi.seed_demo = 'on';` logo após o `begin;` da migração.
