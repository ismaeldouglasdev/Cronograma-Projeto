# Rotação de credenciais

Checklist para trocar as senhas do Neon e do Supabase sem derrubar o app.

> **Contexto:** em 2026-09-25 as connection strings de produção ficaram
> hardcoded em `cronograma/migrate_to_pg.py` e `cronograma/import_to_supabase.py`
> e foram publicadas no histórico do GitHub. O histórico foi reescrito com
> `git-filter-repo` e o repositório tornado público, mas **as senhas precisam
> ser trocadas** — reescrever histórico não desfaz um vazamento.

## A armadilha que quebraria o app

`config.py::_resolve_secret_key()` deriva a chave JWT de `DATABASE_URL` quando
`JWT_SECRET` não está definido:

```python
derived = hashlib.sha256(DATABASE_URL.encode()).hexdigest()
```

Se a chave depende da senha do banco, **trocar a senha invalida todos os
tokens JWT de uma vez** — todo usuário é deslogado e precisa entrar de novo.
Para evitar isso, defina `JWT_SECRET` **antes** de rotacionar. O
`render.yaml` já declara `JWT_SECRET` com `generateValue: true`, o que faz o
Render gerar um valor estável entre deploys.

## Ordem de execução

### 1. Congelar a chave JWT (evita o logout em massa)

Render → serviço `cronograma-projeto` → **Environment**:

- Se `JWT_SECRET` **não** existir, adicione com qualquer valor aleatório longo
  (mínimo 32 caracteres). Sugestão: `openssl rand -hex 32`.
- **Não** redeploy ainda. Só a variável precisa existir no próximo deploy.

### 2. Neon (banco de produção)

1. <https://console.neon.tech> → o projeto que hospeda a base de produção
2. **Roles** → a role de aplicação (a mesma do usuário na connection string
   atual) → *Reset password*
3. Copie a connection string nova.

> Os identificadores do projeto e da role **não** ficam neste arquivo de
> propósito: o repositório é público e eles servem só de alvo. Identifique-os
> pelo seu próprio dashboard ou pela string que o app já usa.

### 3. Supabase

1. <https://supabase.com> → o projeto de destino dos dados do Cronograma
2. **Project Settings → Database → Reset database password**
3. Copie a connection string nova.

### 4. Render (aplicar)

Render → `cronograma-projeto` → **Environment** → atualize `DATABASE_URL` com a
string do passo 2 → **Save & Deploy**.

Se o app também usa o Supabase, crie/atualize a variável correspondente que o
`import_to_supabase.py` consome localmente (`PG_URL` no seu `.env`).

### 5. Verificar

```bash
# app responde
curl -sI https://cronograma-projeto.onrender.com/ | head -1

# nenhum warning de JWT_SECRET nos logs
# Render -> Logs -> procurar "JWT_SECRET ausente"
```

Depois faça login pela interface e confirme que um usuário **antes** da rotação
continua logado. Se alguém cair, `JWT_SECRET` não estava setado no passo 1.

### 6. Credenciais locais

Atualize `cronograma/.env` (não versionado):

```bash
PG_URL=<nova string do Neon>
```

## Se algo der errado

| Sintoma | Causa provável | Ação |
|---|---|---|
| App não sobe, log de conexão recusada | `DATABASE_URL` com senha antiga | Repita o passo 4 |
| Todo mundo deslogado de uma vez | `JWT_SECRET` ausente no passo 1 | Defina `JWT_SECRET` e redeploy; usuários voltam a entrar |
| `/admin/*` retorna 403 | `MIGRATION_SECRET` vazio | É o comportamento esperado (admin bloqueado) |
| App não sobe e o log cita `JWT_SECRET ausente` | Ainda em `derived` | Normal até o passo 1 |

## Prevenção

- `cronograma/.env` e `cronograma/app/data_clean.json` / `data_export.json`
  já estão no `.gitignore`. Não use `git add -f` nesses caminhos.
- Para conferir antes de qualquer push:

  ```bash
  git grep -nE "postgres(ql)?://[^ \"']*:[^ \"'@]*@"
  ```

  Não deve retornar nada. Se retornar, a credencial está prestes a vazar.
