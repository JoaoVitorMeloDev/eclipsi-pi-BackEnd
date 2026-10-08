# Backend EcliPsi


## Configuração

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

## Verificações



```bash
pytest -q
```

```bash
python check_database.py
```

