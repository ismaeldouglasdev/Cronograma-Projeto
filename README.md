# Cronograma de Estudos
<p align="center">
  <strong>🇧🇷 Português</strong> &nbsp;|&nbsp; <a href="README.en.md">🇺🇸 English</a>
</p>


Sistema completo de gerenciamento de estudos com timer Pomodoro integrado, tracking de horas, quadro de horários de aulas e gamificação.

## Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite
- **Frontend:** Vanilla JS + Chart.js
- **Runtime:** Python 3.8+

## Funcionalidades

- **Timer Pomodoro** — Foco de 25min com descanso de 5min, seleção de área/tarefa
- **Áreas/Matérias** — Cadastro com cor, categoria, tipo (online/presencial)
- **Tarefas** — CRUD com prioridade, data de entrega, meta de pomodoros
- **Sessões de Estudo** — Registro manual de tempo por área
- **Gamificação** — XP, coins, streak, achievements, níveis
- **Quadro de Horários** — Grid semanal das aulas presenciais
- **Resumo/Estatísticas** — Gráfico de pizza com horas por área (Chart.js)
- **8 Temas** — Dark, light, ocean, purple, forest, midnight, pastel, contrast

## Como Rodar

### 1. Ativar ambiente virtual

```bash
source .venv/bin/activate
```

### 2. Iniciar servidor

```bash
cd cronograma/app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Acessar

Abra http://localhost:8000 no navegador.

## Estrutura do Projeto

```
Cronograma(Projeto)/
├── cronograma/
│   ├── app/
│   │   ├── main.py              # API FastAPI + banco + gamificação
│   │   ├── static/
│   │   │   ├── index.html       # Interface principal
│   │   │   ├── style.css        # Estilos + temas
│   │   │   ├── app.js           # Lógica do frontend
│   │   │   ├── store.js         # Estado global + gamificação
│   │   │   ├── foco.js          # Timer Pomodoro
│   │   │   ├── auth.js          # Autenticação
│   │   │   └── theme.js         # Gerenciador de temas
│   │   └── cronograma.db        # Banco SQLite
│   ├── requirements.txt
│   ├── docker-compose.yml
│   └── Dockerfile
├── icon_images/                 # Ícones do projeto
└── README.md
```

## API Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/auth/register` | Registrar usuário |
| POST | `/auth/login` | Login (retorna JWT) |
| GET | `/areas` | Listar áreas |
| POST | `/areas` | Criar área |
| PATCH | `/areas/{id}` | Atualizar área |
| DELETE | `/areas/{id}` | Deletar área |
| GET | `/tasks` | Listar tarefas |
| POST | `/tasks` | Criar tarefa |
| PATCH | `/tasks/{id}` | Atualizar tarefa |
| DELETE | `/tasks/{id}` | Deletar tarefa |
| GET | `/sessoes` | Listar sessões |
| POST | `/sessoes` | Criar sessão |
| GET | `/sessoes/resumo` | Resumo por período |
| POST | `/pomodoro/completar` | Completar pomodoro |
| GET | `/gamification-summary` | Resumo de gamificação |
| POST | `/coins/buy-freeze` | Comprar freeze (10 coins) |

## Gamificação

- **XP:** minutos estudados + 5 XP por tarefa concluída
- **Level:** `XP = 100 × level^1.5`
- **Coins:** +3 por pomodoro, +1 a cada 10min de sessão
- **Streak:** dias consecutivos com estudo (freezes disponíveis)
- **Achievements:** categorias XP, streak, pomodoro, tasks, level, coins

## Licença

MIT
