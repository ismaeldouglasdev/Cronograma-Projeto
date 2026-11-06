# Relatório de Bugs e Inconsistências - Cronograma

**Data:** 2026-10-30  
**Analisado por:** Devin AI  
**Projeto:** Cronograma - Sistema de gerenciamento de estudos com gamificação

---

## ✅ CORREÇÕES APLICADAS (2026-10-30)

### Bug #1: Validação de Senha - CORRIGIDO ✅
**Arquivos:** middleware.py, auth_service.py, auth.js
**Correção:** Todas as validações agora exigem 8 caracteres, 1 letra, 1 número, 1 caractere especial.

### Bug #2: XP Não Sincronizado - CORRIGIDO ✅
**Arquivos:** store.js
**Correção:** XP agora é obtido exclusivamente do backend via `syncFromBackend()`.

### Bug #3: Streak Local vs Backend - CORRIGIDO ✅
**Arquivos:** store.js
**Correção:** Streak agora é obtido exclusivamente do backend.

### Bug #4: JWT Secret Derivado de DATABASE_URL - CORRIGIDO ✅
**Arquivos:** config.py
**Correção:** Em produção, ausência de JWT_SECRET causa ValueError.

### Bug #6: Validação de Datas no Resumo - CORRIGIDO ✅
**Arquivos:** sessoes.py
**Correção:** Datas inválidas agora logam warning.

### Bug #7: Auth.js Parse JWT - CORRIGIDO ✅
**Arquivos:** auth.js
**Correção:** Erros de parse JWT agora logam console.error.

### Bug #4 (segundo): Cleanup de Guests - CORRIGIDO ✅
**Arquivos:** gamification_service.py
**Correção:** Queries de delete usam synchronize_session="fetch".

### Bug #15: Validação de Duração Mínima - CORRIGIDO ✅
**Arquivos:** sessoes.py
**Correção:** Sessões exigem mínimo 5 minutos.

### Inconsistência #16: Conquistas Locais - CORRIGIDO ✅
**Arquivos:** store.js
**Correção:** Conquistas buscadas do backend, definição local removida.

### Código Morto #19-20: Funções Deprecated - CORRIGIDO ✅
**Arquivos:** store.js
**Correção:** syncStatsFromData e addCoins removidos da API pública.

### Segurança #14: Rate Limit Auth - JÁ IMPLEMENTADO ✅
**Arquivos:** auth.py
**Status:** Já tinha rate limit (login: 10/min, register: 20/min).

### UI/UX #9: Feedback ao Comprar Freeze - JÁ IMPLEMENTADO ✅
**Arquivos:** app.js
**Status:** Já tinha toast de sucesso em comprarFreeze().

### UI/UX #10: Erros de Rede no Modal Pomodoro - CORRIGIDO ✅
**Arquivos:** foco.js
**Correção:** Erros agora mostram toast não-blocante e resetam timer.

### UI/UX #12: Indicadores de Carregamento - CORRIGIDO ✅
**Arquivos:** app.js
**Correção:** Adicionada função setLoading() aplicada em loadAreas, loadTasks, loadSessoes.

---

## ✅ CORREÇÕES APLICADAS (2026-11-06)

### Bug crítico: SyntaxError em routes/auth.py — CORRIGIDO ✅
**Arquivo:** routes/auth.py (`google_callback`)
**Problema:** O corpo do callback estava fora do `try`, deixando o `except` órfão — `import main` falhava e o app inteiro não subia (presente no HEAD/deploy).
**Correção:** Corpo do callback indentado para dentro do `try`.

### Bug crítico: SyntaxError em routes/gamification.py — CORRIGIDO ✅
**Arquivo:** routes/gamification.py
**Problema:** `"total_pomodoros": pomodoros,"` (aspas extra) e o decorator `@router.post("/coins/add")` tinha sido substituído pelo endpoint `/roadmap/xp`, deixando `add_coins` sem rota.
**Correção:** Aspas removidas e decorator restaurado.

### Bug: Link externo "RoadmapMaster" quebrava a navegação — CORRIGIDO ✅
**Arquivo:** static/app.js (`initTabs`)
**Problema:** O `<a class="sidebar-link">` sem `data-tab` chamava `switchToTab(undefined)`, desativando todos os painéis.
**Correção:** Handler ignora sidebar-links sem `data-tab`.

### Bug: Aba "Roadmap (embed)" inacessível via hash — CORRIGIDO ✅
**Arquivo:** static/app.js, static/i18n.js
**Correção:** `'roadmap'` adicionado a `VALID_TABS` e `getPageTitle`; chaves `pages.roadmap` (pt/en) criadas.

### Bug: CSP bloqueava o iframe do Roadmap — CORRIGIDO ✅
**Arquivo:** middleware.py
**Problema:** Sem `frame-src`, `default-src 'self'` impedia carregar `ismaeldouglasdev.github.io`.
**Correção:** `frame-src 'self' https://ismaeldouglasdev.github.io` adicionado.

### Bug: i18n sem `pwd_rule_special` — CORRIGIDO ✅
**Arquivo:** static/i18n.js
**Problema:** Checklist de senha exibiria a chave crua após a nova regra de caractere especial.
**Correção:** Traduções pt/en adicionadas.

### Bug: `/auth/google` retornava 500 sem OAuth configurado — CORRIGIDO ✅
**Arquivo:** routes/auth.py
**Correção:** Redireciona para `/app?error=oauth_not_configured` (tratado pelo frontend).

### Testes desatualizados (política de senha) — CORRIGIDO ✅
**Arquivo:** test_api.py
**Problema:** Testes assumiam caractere especial opcional; a política vigente (JS + backend) exige caractere especial.
**Correção:** `VALID_SENHA` com caractere especial, novo teste de rejeição sem especial, caso `sem_especial` no parametrize e asserções de paridade JS/Python atualizadas. Suíte: 87 testes passando.

---

## 📋 Resumo Atualizado (2026-10-30)

| Categoria | Original | Corrigidos | Pendentes |
|-----------|----------|------------|-----------|
| Bugs Críticos | 4 | 4 | 0 |
| Bugs Menores | 4 | 4 | 0 |
| Inconsistências UI/UX | 4 | 3 | 1 |
| Segurança | 3 | 3 | 0 |
| Inconsistências de Dados | 3 | 3 | 0 |
| Código Morto | 2 | 2 | 0 |
| **Total** | **20** | **19** | **1** |

## ✅ Conclusão

**19 de 20 bugs/inconsistências foram corrigidos (95%)**

### Correções Aplicadas:
- ✅ Validação de senha unificada (8 chars, letra, número, especial)
- ✅ XP e streak agora são SSOT no backend
- ✅ JWT_SECRET obrigatório em produção
- ✅ Validação de duração mínima em sessões (5 min)
- ✅ Cleanup de guests com synchronize_session
- ✅ Conquistas buscadas do backend
- ✅ Código morto removido da API pública
- ✅ Logs de erro adicionados para debug
- ✅ Rate limit para auth já implementado (login: 10/min, register: 20/min)
- ✅ Feedback visual ao comprar freeze já existia
- ✅ Erros de rede no modal de pomodoro usam toast não-blocante
- ✅ Indicadores de carregamento adicionados em loadAreas, loadTasks, loadSessoes

### Pendente (Muito Baixa Prioridade):
- 🔲 Melhoria de precisão do timer com Page Visibility API (mitigado por Date.now())

---

**Observações Gerais:**
- O código é bem estruturado com separação clara de responsabilidades
- O sistema de gamificação agora usa o backend como SSOT em todas as áreas
- Autenticação com JWT e refresh tokens está bem implementada
- O sistema de rate limiter com persistência é robusto
- Existem testes automatizados que validam partes importantes do sistema
- As correções aplicadas melhoram significativamente a consistência entre frontend e backend
- 95% dos bugs originais foram corrigidos
