# Cronograma Project

## Visão Geral
Sistema de gerenciamento de tarefas e estudos com timer Pomodoro integrado, tracking de horas de estudo, e quadro de horários de aulas.

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
- Tabelas: `areas`, `tasks`, `sessoes`

## Estrutura das Tabelas

### Areas
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária |
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
| area_id | INTEGER | FK para areas |
| duracao_minutos | INTEGER | Duração em minutos |
| data | DATE | Data da sessão |
| task_id | INTEGER | FK opcional para tasks |

## Endpoints da API

### Áreas
- `GET /areas` - Listar todas as áreas
- `POST /areas` - Criar área
- `PATCH /areas/{id}` - Atualizar área
- `DELETE /areas/{id}` - Deletar área (cascata para tasks/sessões)

### Tarefas
- `GET /tasks` - Listar todas as tarefas
- `POST /tasks` - Criar tarefa
- `PATCH /tasks/{id}` - Atualizar tarefa (todos os campos)
- `DELETE /tasks/{id}` - Deletar tarefa

### Sessões de Estudo
- `GET /sessoes` - Listar todas as sessões
- `POST /sessoes` - Criar sessão manualmente
- `PATCH /sessoes/{id}` - Atualizar sessão
- `DELETE /sessoes/{id}` - Deletar sessão
- `GET /sessoes/resumo` - Resumo de horas por área

### Pomodoro
- `POST /pomodoro/completar` - Registrar pomodoro completo (cria sessão + incrementa contador da tarefa)

## Funcionalidades Principais

### Timer Pomodoro (Foco)
- Timer configurável (padrão: 25min foco, 5min descanso)
- Seleção de área e tarefa específica
- Descanso automático opcional
- Persistência de estado no localStorage
- Recuperação de timer ao retornar à página
- Estatísticas do dia (sessões completadas, tempo total)
- Meta de pomodoros por tarefa com progresso visual

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
- Ao marcar como concluída, pede duração e cria sessão automaticamente
- Ordenação por prioridade ou data
- Filtro de busca por nome

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

## Arquivos Importantes
- `cronograma/app/main.py` - API e lógica de banco
- `cronograma/app/static/app.js` - Lógica do frontend
- `cronograma/app/static/foco.js` - Módulo do timer Pomodoro
- `cronograma/app/static/index.html` - Interface principal
- `cronograma/app/static/style.css` - Estilos
- `cronograma/iniciar_cronograma.bat` - Script de inicialização

## Convenções de Código

### Python (main.py)
- Type hints onde possível
- Padrão PEP 8
- SQLAlchemy ORM com declarative base
- Pydantic para schemas de request/response

### JavaScript
- ES6+ (const/let, arrow functions, async/await)
- Template literals para geração de HTML
- camelCase para funções/variáveis
- Módulo IIFE para o timer (FocoTimer)

### CSS
- CSS custom properties para cores
- Mobile-first
- Flexbox para layouts

## Fluxo de Desenvolvimento

### Commits
- Mensagens claras e descritivas
- Verbo inicial: "Add", "Fix", "Update", "Remove"
- Exemplo: "Add edit modal for study sessions"

### Fazendo Alterações
1. Backend em `main.py` - servidor recarrega com `--reload`
2. Frontend em `static/` - atualizar browser
3. Migrações adicionadas em main.py via ALTER TABLE (SQLite)

### Problemas Comuns
- Imports falham: garantir que está no diretório `cronograma/app`
- Página não carrega: verificar caminho no batch file
- Dados faltando: verificar local do banco de dados
