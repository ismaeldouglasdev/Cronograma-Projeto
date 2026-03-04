# Cronograma Project

## Visão Geral
Sistema de gerenciamento de tarefas e estudos com timer Pomodoro integrado, tracking de horas de estudo, quadro de horários de aulas e sistema completo de gamificação (XP, coins, achievements, streak).

## Stack Tecnológico
- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: Vanilla JS + Chart.js
- **Runtime**: Python

## Como Executar

### Pré-requisitos
- Python 3.8+

### Instalação
```bash
pip install fastapi uvicorn sqlalchemy pydantic
```

### Iniciar Servidor
```bash
cd cronograma/app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Ou usar o arquivo batch:
```bash
cronograma/iniciar_cronograma.bat
```

### Acessar
- Local: http://localhost:8000

## Banco de Dados
- Localização: `cronograma/app/cronograma.db`
- Tabelas: `areas`, `tasks`, `sessoes`, `users`, `achievements`, `user_achievements`

## Estrutura das Tabelas

### Users
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária |
| email | VARCHAR(255) | Email único |
| password_hash | VARCHAR(255) | Hash da senha |
| is_verified | BOOLEAN | Email verificado |
| current_streak | INTEGER | Dias seguidos atuais |
| longest_streak | INTEGER | Maior sequência |
| streak_freezes | INTEGER | Freezes disponíveis (max 4) |
| coins | INTEGER | Moedas acumuladas |
| last_activity_date | VARCHAR(20) | Última atividade |

### Areas
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária |
| user_id | INTEGER | FK para users |
| nome | VARCHAR(255) | Nome da área/matéria |
| cor | VARCHAR(20) | Cor hexadecimal |
| ordem | INTEGER | Ordem de exibição |
| tipo | VARCHAR(20) | "online" ou "presencial" |
| dia_semana | VARCHAR(20) | Dia da semana (presencial) |
| horario | VARCHAR(50) | Horário da aula |
| sala | VARCHAR(50) | Sala/ sala de aula |
| bloco | VARCHAR(50) | Bloco do prédio |
| professor | VARCHAR(255) | Nome do professor |
| subcategoria | VARCHAR(100) | Categoria opcional |

### Tasks
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária |
| user_id | INTEGER | FK para users |
| area_id | INTEGER | FK para areas |
| titulo | VARCHAR(255) | Título da tarefa |
| descricao | VARCHAR(500) | Descrição opcional |
| data_entrega | DATE | Data de entrega |
| concluida | BOOLEAN | Status de conclusão |
| duracao_minutos | INTEGER | Tempo gasto (quando concluída) |
| prioridade | INTEGER | 1=baixa, 2=média, 3=alta |
| meta_pomodoros | INTEGER | Meta de pomodoros para a tarefa |
| pomodoros_concluidos | INTEGER | Contador de pomodoros feitos |

### Sessoes
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária |
| user_id | INTEGER | FK para users |
| area_id | INTEGER | FK para areas |
| duracao_minutos | INTEGER | Duração em minutos |
| data | DATE | Data da sessão |
| task_id | INTEGER | FK opcional para tasks |

### Achievements
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária |
| nome | VARCHAR(255) | Nome da conquista |
| descricao | VARCHAR(500) | Descrição |
| categoria | VARCHAR(50) | xp, streak, pomodoro, tasks, level, coins |
| requisito | INTEGER | Valor necessário |
| icone | VARCHAR(50) | Ícone visual |

## Endpoints da API

### Áreas
- `GET /areas` - Listar todas as áreas
- `POST /areas` - Criar área
- `PATCH /areas/{id}` - Atualizar área (requer user_id)
- `DELETE /areas/{id}` - Deletar área (requer user_id)

### Tarefas
- `GET /tasks` - Listar todas as tarefas
- `POST /tasks` - Criar tarefa
- `PATCH /tasks/{id}` - Atualizar tarefa (requer user_id)
- `DELETE /tasks/{id}` - Deletar tarefa (requer user_id)

### Sessões de Estudo
- `GET /sessoes` - Listar todas as sessões
- `POST /sessoes` - Criar sessão manualmente (+coins, atualiza streak)
- `PATCH /sessoes/{id}` - Atualizar sessão (requer user_id)
- `DELETE /sessoes/{id}` - Deletar sessão (requer user_id)
- `GET /sessoes/resumo?start=YYYY-MM-DD&end=YYYY-MM-DD` - Resumo por período

### Pomodoro
- `POST /pomodoro/completar` - Registrar pomodoro (+3 coins, atualiza streak/conquistas)

### Gamificação
- `GET /gamification-summary` - Retorna XP, level, streak, coins, achievements

### Coins
- `POST /coins/buy-freeze` - Comprar freeze (10 coins)
- `POST /coins/add?amount=N` - Adicionar coins (testes)

## Sistema de Gamificação

### XP (Experiência)
- XP = minutos estudados + 5 XP por tarefa concluída
- Level = calculado por curva: XP = 100 * level^1.5

### Coins
- +3 coins por pomodoro completado
- +1 coin a cada 10 minutos de sessão manual
- Custo de freeze: 10 coins

### Streak
- Baseado em dias distintos com sessões
- Freezes: ganha 1 por semana (max 4)
- Pode usar freeze para manter streak em dias sem atividade

### Achievements
Categorias:
- **XP**: 100, 500, 1000, 5000, 10000 XP
- **Streak**: 3, 7, 14, 30, 100 dias
- **Pomodoro**: 1, 10, 50, 100, 500 pomodoros
- **Tasks**: 1, 10, 50, 100, 500 tarefas
- **Level**: 2, 5, 10, 25, 50
- **Coins**: 10, 50, 100, 500, 1000 coins

## Funcionalidades Principais

### Timer Pomodoro (Foco)
- Timer configurável (padrão: 25min foco, 5min descanso)
- Seleção de área e tarefa específica
- Descanso automático opcional
- Persistência de estado no localStorage
- Recuperação de timer ao retornar à página
- Estatísticas do dia (sessões completadas, tempo total)
- Meta de pomodoros por tarefa com progresso visual
- Web Audio API para som persistente
- Atualização do título da aba com timer
- Botão "Encerrar agora"

### Áreas/Matérias
- Criação com cor, categoria (subcategoria)
- Tipos: Online ou Presencial
- Campos para aulas presenciais: dia, horário, sala, bloco, professor
- Edição e exclusão via modal

### Tarefas
- Título, descrição, data de entrega
- Prioridade (baixa, média, alta)
- Meta de pomodoros opcional
- Checklist de conclusão
- Ordenação por prioridade ou data
- Filtro de busca por nome

### Dashboard Layout
- Sidebar fixa à esquerda (desktop)
- Navegação por ícones
- Mini stats (level, XP, streak)
- Responsivo: sidebar reduz em tablet, vira barra inferior em mobile

### Temas
- 8 temas: dark, light, ocean, purple, forest, midnight, pastel, contrast
- Seletor sincronizado entre header e sidebar

### Quadro de Horários
- Visualização em grid dos horários presenciais
- Agrupamento por dia da semana

### Sessões de Estudo
- Registro manual de tempo estudado
- Associação com área (obrigatório)
- Associação com tarefa (opcional)
- Edição e exclusão via modal

### Resumo/Estatísticas
- Gráfico de pizza com horas por área (Chart.js)
- Lista detalhada com total de minutos e horas
- Filtro por período (data inicial e final)

## Arquivos Importantes
- `cronograma/app/main.py` - API, banco, gamificação
- `cronograma/app/static/app.js` - Lógica do frontend
- `cronograma/app/static/store.js` - Estado global com gamificação
- `cronograma/app/static/foco.js` - Módulo do timer Pomodoro
- `cronograma/app/static/theme.js` - Gerenciador de temas
- `cronograma/app/static/index.html` - Interface principal
- `cronograma/app/static/style.css` - Estilos (dashboard, themes)
- `cronograma/iniciar_cronograma.bat` - Script de inicialização

## Convenções de Código

### Python (main.py)
- Type hints onde possível
- Padrão PEP 8
- SQLAlchemy ORM com declarative base
- Pydantic para schemas de request/response
- Validação de user_id em todos os endpoints PATCH/DELETE

### JavaScript
- ES6+ (const/let, arrow functions, async/await)
- Template literals para geração de HTML
- camelCase para funções/variáveis
- Módulo IIFE para o timer (FocoTimer)
- Funções utilitárias: formatDate(), formatDuration()

### CSS
- CSS custom properties para cores (temas)
- Mobile-first
- Flexbox para layouts
- Layout dashboard com sidebar

## Fluxo de Desenvolvimento

### Commits
- Mensagens claras e descritivas
- Verbo inicial: "Add", "Fix", "Update", "Remove"
- Exemplo: "Add coins system and buy-freeze endpoint"

### Fazendo Alterações
1. Backend em `main.py` - servidor recarrega com `--reload`
2. Frontend em `static/` - atualizar browser
3. Migrações adicionadas em main.py via ALTER TABLE (SQLite)

### Problemas Comuns
- Imports falham: garantir que está no diretório `cronograma/app`
- Página não carrega: verificar caminho no batch file
- Dados faltando: verificar local do banco de dados

## Bugs Corrigidos (Refatoração 2024)

1. **XP inconsistente**: Mudou de 1 XP/min + 50 XP/task para minutos + 5 XP/task
2. **Task PATCH criava sessões**: Removido - sessões só via endpoints próprios
3. **Streak frágil**: Agora baseado em datas reais de sessões
4. **Segurança**: user_id validado em todos endpoints PATCH/DELETE
5. **Classe duplicada**: Removido SessaoCreate duplicado
