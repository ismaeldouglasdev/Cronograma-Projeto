# Cronograma de Estudos

Sistema de gerenciamento de estudos com timer Pomodoro, tarefas, metas por área, gamificação e estatísticas.

- **Produção:** https://cronograma-projeto.onrender.com/
- **Repositório:** https://github.com/ismaeldouglasdev/Cronograma-Projeto
- **Stack:** FastAPI + SQLAlchemy (SQLite local / PostgreSQL em produção) + frontend estático (Vanilla JS)

## Estado atual (local verificado em 2026-11-18)

- API versionada em `/api/v1/*` com compatibilidade para rotas legadas na raiz (transição segura).
- Health check: `GET /health` e `GET /api/v1/health`.
- Métricas Prometheus: `GET /metrics` e `GET /api/v1/metrics`.
- Auth disponível em `/auth/*` e `/api/v1/auth/*` (OAuth/callbacks e cookies mantidos no fluxo raiz).
- Melhorias recentes no código local (não commitadas): WAL no SQLite, endurecimento de JWT/rate limit, otimizações de queries sociais, ajustes de testes e alinhamento do frontend para `/api/v1`.
- Migrações Alembic presentes em `cronograma/alembic/` (arquivos locais não rastreados no momento desta verificação).

> Observação: a produção pode estar em versão anterior até novo deploy. No momento da verificação, o site respondia 200 em `/` e `/app`, mas `/health` ainda retornava 404 em produção.

## Estrutura principal

```text
cronograma/
  app/                 # aplicação FastAPI + frontend estático
    main.py            # entrypoint FastAPI, middlewares, roteamento
    config.py          # env, DB, segurança, CORS, rate-limit config
    middleware.py      # segurança, logging, rate limiting
    routes/            # rotas (auth, areas, tasks, sessoes, gamification, stats, missions, social, admin)
    services/          # regras de negócio
    models/            # modelos/schemas
    static/            # frontend (index/landing/js/css/assets)
    test_*.py          # testes (pytest + httpx ASGI)
  alembic/             # migrações
  alembic.ini
  requirements.txt
  requirements-dev.txt
  render.yaml          # config de deploy (Render)
```

## Como rodar localmente

### 1) Ambiente Python

Use um virtualenv com dependências instaladas (ex.: `cronograma/venv` ou `cronograma/.venv`).

```bash
cd cronograma
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# opcional para dev/testes extras:
# pip install -r requirements-dev.txt pytest pytest-asyncio
```

### 2) Variáveis de ambiente

Crie `cronograma/.env` (ou exporte variáveis). Exemplo mínimo:

```env
ENVIRONMENT=development
JWT_SECRET=troque-por-uma-string-aleatoria-longa
DATABASE_URL=sqlite:///./cronograma.db
APP_URL=http://localhost:8000
```

Variáveis relevantes (ver `.env.example`): `GOOGLE_CLIENT_ID/SECRET/REDIRECT_URI`, `RESEND_API_KEY`, `EMAIL_FROM`, `MIGRATION_SECRET`, rate limit (`RATE_LIMIT_*`), etc.

### 3) Iniciar servidor

O app usa imports relativos ao diretório `app/` (padrão do deploy atual):

```bash
cd cronograma/app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Acesse: http://localhost:8000/

## Endpoints úteis

- `GET /` landing
- `GET /app` aplicação
- `GET /health` (e `/api/v1/health`) status + conectividade do banco
- `GET /metrics` (e `/api/v1/metrics`) métricas Prometheus
- `POST /auth/register`, `POST /auth/login`, etc. (também em `/api/v1/auth/*`)
- APIs principais em `/api/v1/*`: `areas`, `tasks`, `sessoes`, `gamification-summary`, `missions`, `stats/heatmap`, `stats/analytics`, rotas sociais etc.

## Testes

Os testes rodam a partir de `cronograma/app` (imports esperam esse contexto):

```bash
cd cronograma/app
pytest -q
# ou, usando venv específico:
# ../venv/bin/python -m pytest -q
```

Validação rápida recomendada antes de deploy:
- `test_security_headers.py`
- `test_api.py`
- `test_e2e_critical.py`
- `test_email_verification.py`
- `test_password_reset.py`
- `test_token_revocation.py`
- `test_rate_limit_persist.py`

## Deploy (Render)

`render.yaml` define:
- `rootDir: cronograma`
- build: `pip install -r requirements.txt`
- start: `cd app && uvicorn main:app --host 0.0.0.0 --port $PORT --forwarded-allow-ips=""`

Segredos/configurações sensíveis devem ser definidos no dashboard do Render (nunca versionados).

## Organização local (nota)

- **Repo de desenvolvimento ativo:** `~/projetos/cronograma` (este diretório).
- **Pasta paralela no Desktop:** `~/Desktop/code_study/MeusProjetos/Cronograma(Projeto)` contém artefatos/backup (`cronograma.divergent.bak-*`, waitlist) e não deve ser tratada como fonte atual sem verificação; evite operações destrutivas ao reconciliar.

## Licença

MIT
