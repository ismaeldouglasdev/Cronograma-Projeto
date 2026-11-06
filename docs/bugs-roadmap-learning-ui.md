# Relatório de Bugs - roadmap-learning-ui (Projeto Incorreto)

> **Nota:** Este relatório foi gerado para o projeto `roadmap-learning-ui` por engano. O projeto correto é `cronograma`. Este arquivo foi preservado para referência, mas não deve ser usado para o projeto Cronograma.

---

## 🐛 Bugs e Inconsistências Encontrados

### 1. **Inconsistência de Tipos no Generator** (CRÍTICO)
**Arquivo:** `src/App.tsx` linha 415-422 e `src/types.ts` linha 190-197

**Problema:** O tipo `QuestionnaireAnswers` em `types.ts` define campos com valores específicos (ex: `level: 'iniciante' | 'intermediario' | 'avancado'`), mas em `App.tsx` o código usa string diretiva do questionário que retorna valores como `'Iniciante'`, `'Intermediário'`, `'Avançado'` (com acentos e maiúsculas).

**Impacto:** O gerador de roadmap pode não funcionar corretamente se receber valores que não batem com os tipos esperados.

**Localização:**
- `src/types.ts` linhas 190-197
- `src/features/ai-generator/questions.ts` linhas 18-55
- `src/App.tsx` linhas 415-422

---

### 2. **Filtro de Dificuldade Não Funciona** (BUG)
**Arquivo:** `src/features/search/SearchBar.tsx` linhas 111-123 e `src/App.tsx` linhas 447-457

**Problema:** O filtro de dificuldade (`difficulty`) está implementado na UI mas **nunca é usado** na lógica de busca. Em `App.tsx`, o `searchFiltered` filtra por `type` e `completion`, mas ignora completamente `difficulty`.

**Impacto:** Usuários podem selecionar filtros de dificuldade mas eles não têm efeito nenhum.

**Localização:**
- `src/features/search/SearchBar.tsx` linhas 111-123 (filtro renderizado)
- `src/App.tsx` linhas 447-457 (filtro não aplicado)

---

### 3. **Quiz Modal Não Usa `alreadyPassed`** (BUG)
**Arquivo:** `src/App.tsx` linha 557 e `src/components/QuizModal.tsx` linha 40

**Problema:** O `QuizModal` tem uma prop `alreadyPassed` que determina se deve mostrar mensagem de revisão sem XP, mas em `App.tsx` ao abrir o modal essa prop nunca é passada.

**Impacto:** Usuários podem ganhar XP repetidamente ao fazer o mesmo quiz sem verificação.

**Localização:**
- `src/App.tsx` linha 557
- `src/components/QuizModal.tsx` linha 22, 98-100

---

### 4. **SkillModal Não Recebe `hasQuiz`** (BUG)
**Arquivo:** `src/App.tsx` linha 548 e `src/components/SkillModal.tsx` linha 8

**Problema:** O `SkillModal` tem uma prop `hasQuiz` para desabilitar o botão de quiz quando não há quiz disponível, mas em `App.tsx` essa prop nunca é passada (usa default `true`).

**Impacto:** Botão de quiz aparece mesmo quando não há quiz para a skill, levando a erro ou vazio.

**Localização:**
- `src/App.tsx` linha 548
- `src/components/SkillModal.tsx` linha 8, 52

---

### 5. **hasLesson() Sempre Retorna True** (INCONSISTÊNCIA)
**Arquivo:** `src/data/lessons.ts` linha 338

**Problema:** A função `hasLesson()` sempre retorna `true` com comentário "Generator handles any topic", mas isso é inconsistente porque:
1. Nem todos os tópicos têm lições pré-definidas
2. O gerador pode falhar ou não gerar lição válida
3. Isso causa que o botão de lição apareça para todos os tópicos, mesmo sem conteúdo

**Impacto:** Botão de lição aparece para tópicos que podem não ter lição funcional.

**Localização:**
- `src/data/lessons.ts` linha 338
- `src/components/TopicRow.tsx` linha 39

---

### 6. **Ortografia Inconsistente** (UI/UX)
**Arquivo:** `src/components/SubModCard.tsx` linhas 16, 23, 24, 35

**Problema:** Textos em português sem acento:
- "Facil" → deveria ser "Fácil"
- "Medio" → deveria ser "Médio"
- "Dificil" → deveria ser "Difícil"
- "exercicios" → deveria ser "exercícios"

**Impacto:** Erros ortográficos visíveis na UI.

**Localização:**
- `src/components/SubModCard.tsx` linhas 16, 23, 24, 35

---

### 7. **Stats Component - Texto Inconsistente** (UI/UX)
**Arquivo:** `src/components/Stats.tsx` linha 20

**Problema:** Texto "XP p/ proximo" sem acento e abreviação inconsistente. Deveria ser "XP para o próximo" ou pelo menos "XP p/ próximo".

**Impacto:** Erro ortográfico visível.

**Localização:**
- `src/components/Stats.tsx` linha 20

---

### 8. **LessonModal - Duplicate Class Names** (UI/UX MENOR)
**Arquivo:** `src/components/LessonModal.tsx` linhas 367-368

**Problema:** Linha 367 e 368 têm `dark:text-cream-100` duplicado: `dark:text-cream-100 dark:text-cream-100`.

**Impacto:** Visualmente não afeta, mas é código redundante.

**Localização:**
- `src/components/LessonModal.tsx` linhas 367-368

---

### 9. **Quiz Modal - XP Pago Mesmo Se Já Passou** (LÓGICA)
**Arquivo:** `src/App.tsx` linha 557

**Problema:** O `onComplete` no quiz é chamado com XP independentemente de `alreadyPassed`. O modal mostra mensagem de revisão sem XP visualmente, mas o XP ainda é creditado porque o callback não verifica isso.

**Impacto:** Possível exploração para ganhar XP repetido (embora o `quizResults` deva prevenir, a lógica é redundante).

**Localização:**
- `src/App.tsx` linha 557
- `src/components/QuizModal.tsx` linhas 76-79

---

### 10. **Filtro de Favoritos Pode Deixar Fases Vazias** (UI/UX)
**Arquivo:** `src/App.tsx` linha 460

**Problema:** Ao filtrar por favoritos, se uma fase não tiver tópicos favoritos em nenhuma skill, a fase fica com array de skills vazio. Isso é filtrado depois, mas pode causar flicker ou comportamento estranho.

**Impacto:** Visualmente pode parecer que fases desapareceram sem explicação.

**Localização:**
- `src/App.tsx` linha 460

---

### 11. **Quiz Resultados Não Verificados Antes de Pagar XP** (LÓGICA POTENCIAL)
**Arquivo:** `src/App.tsx` linha 557

**Problema:** O sistema de `quizResults` existe para evitar pagar XP duas vezes, mas no handler do quiz o XP é pago baseado apenas em `outcome.passed`, sem verificar se já estava em `quizResults`.

**Impacto:** Teoricamente possível pagar XP repetido se o estado não estiver sincronizado corretamente.

**Localização:**
- `src/App.tsx` linha 557
- Linhas 291-292 (onde quizResults é usado)

---

### 12. **Generator - Mapeamento de Subáreas Case-Sensitive** (BUG)
**Arquivo:** `src/features/ai-generator/generator.ts` linha 140

**Problema:** O `exerciseTemplates[subArea.toLowerCase()]` usa case-insensitive, mas o lookup em `questionTemplates` (linha 225) usa `skillName.toLowerCase()` diretamente. Se o subArea vier com capitalização diferente, pode não encontrar o template.

**Impacto:** Roadmaps gerados podem ter templates genéricos em vez de específicos para o assunto.

**Localização:**
- `src/features/ai-generator/generator.ts` linhas 140, 225

---

## 📊 Resumo

| Categoria | Quantidade |
|-----------|-----------|
| Bugs Críticos | 4 |
| Bugs Menores | 4 |
| Inconsistências UI/UX | 4 |
| **Total** | **12** |

## 🔧 Recomendações de Prioridade

1. **Alta Prioridade:** Corrigir inconsistência de tipos no Generator (#1) e filtro de dificuldade não funcional (#2)
2. **Média Prioridade:** Corrigir propriedades não usadas nos modais (#3, #4) e ortografia (#6, #7)
3. **Baixa Prioridade:** Limpeza de código redundante (#8) e ajustes de UX (#10)

---

**Data:** 2026-10-30
**Analisado por:** Devin AI
**Status:** Arquivo preservado para referência (projeto incorreto)
