# Posicionamento — Cronograma (cronograma-projeto.onrender.com)

> Estratégia de posicionamento para venda do SaaS. Documento de marketing — **não altera código.**
> Data: 2026-11-14 · Baseado em: app público (/app), landing (onrender.com/), README.md/README.en.md, AGENTS.md, render.yaml, `waitlist/CONTENT-STRATEGY.md`, `waitlist/APP-IMPROVEMENTS.md`, repo GitHub `ismaeldouglasdev/Cronograma-Projeto`.
> **Regra deste documento:** nenhum número, cliente, depoimento, prêmio, integração ou funcionalidade foi inventado. Tudo que não pôde ser confirmado está marcado **«a validar»**.

---

## O que o produto é (fatos verificados)

**Cronograma** é um sistema web de gerenciamento de estudos (FastAPI + PostgreSQL em produção, frontend Vanilla JS + Chart.js) com:

- **Organização:** áreas/matérias (cor, categoria, tipo online/presencial, com sala/bloco/professor/horário para aulas presenciais), tarefas com prioridade, data de entrega e meta de pomodoros, quadro de horários semanal.
- **Foco:** timer Pomodoro configurável (foco/descanso), som ambiente, descanso automático, meta de pomodoros por tarefa.
- **Registro:** sessões manuais de estudo, analytics de 30 dias (min/dia ativo, melhor dia, tendência diária, distribuição por área, por dia da semana, heatmap de atividade).
- **Gamificação:** XP, coins, níveis, conquistas, streak com "freezes" (loja interna, 10 coins), missões diárias (3/dia), ranking em ligas (com promoção/rebaixamento), amigos, clubes, feed de atividade.
- **Acesso:** login por email/senha (verificação via Resend, recuperação de senha), Google OAuth, **modo convidado** com upgrade para conta real **sem perda de dados**.
- **Produto:** 100% gratuito, sem anúncios, open source (MIT), bilíngue PT/EN, 8 temas, responsivo (sidebar vira barra inferior no mobile), web (não há app nativo).

**Estado comercial hoje:** a landing pública ainda diz "100% grátis • Open Source" e a FAQ afirma que "não há planos pagos" — mensagem em transição (ver Decisões abaixo). A landing de lista de espera (`cronogramapro.vercel.app`) retorna 404 — pode nunca ter sido publicada.

**Objetivo declarado pelo usuário:** vender este SaaS por marketing, 100% orgânico.

---

## Decisões de negócio confirmadas (14/11/2026)

| Decisão | Confirmado |
|---|---|
| Modelo de receita | Freemium: **Free** é o padrão (chama o usuário para dentro e ativa); **Pro** é o upgrade com muito valor entregue; **Ultra** fica para o futuro |
| Preço Pro | **R$ 20/mês** (definido pelo dono do produto) |
| Preço Ultra | **R$ 50/mês** — futuro; **«a validar»**: sem data nem definição de recursos |
| Marketing | **100% orgânico** nesta fase (sem verba de mídia paga) |
| Landing | **Autorizado** reposicionar a mensagem de "100% grátis • Open Source" para orientação a valor/resultado |

> **Regra de confiança deste documento:** vender só o que existe. O plano Pro (R$ 20/mês) só pode ser cobrado quando as features premium estiverem implementadas — até lá, a landing fala em "em breve". A sequência de implementação e o funil estão em `marketing/plano-crescimento-organico.md`.

---

## Política de licença e monetização (open source + SaaS pago)

**Posição firmada em 15/11/2026:** sim, é possível cobrar por um projeto open source. Não é contradição: o que se vende é o serviço (hosting gerenciado, dados seguros, features avançadas), não o código. Precedentes sólidos no mercado: GitLab, VS Code, WordPress.com e Ghost.

**As duas promessas que sustentam a política (já comunicadas na landing):**

1. **O código permanece MIT e aberto para sempre.** O repo público continua completo e auditável. Nada publicado até hoje muda de licença.
2. **O Free do serviço hospedado é grátis para sempre.** O Pro (R$ 20/mês) cobra apenas features de profundidade (histórico 365d, analytics avançado, relatórios, subtarefas, missões premium). Nunca o básico de estudar (matérias, tarefas, pomodoro, gamificação).

**Por que o MIT não quebra a venda:**
- O usuário real (universitário) não faz self-host: paga por conveniência e confiança, não por código.
- Open source reduz a fricção de confiança ("dá para auditar") e vira canal de aquisição (estudantes de TI).
- Quem copia o repo não copia marca, distribuição nem velocidade de lançamento.

**Risco e gatilho futuro:**
- Risco do MIT: qualquer pessoa pode hospedar o projeto e cobrar (inclusive oferecendo as features do Pro de graça). Na prática, risco baixo neste público.
- **Gatilho para mudar:** se surgir clonagem/comercialização real por terceiros, os *módulos Pro novos* entram com licença que protege o serviço (AGPL ou dual license), mantendo o código atual MIT. Nunca retroagir licenças já publicadas.
- **Decisão de hoje:** manter MIT em tudo (opção A). Revisitar apenas com evidência de clonagem.

**Regras de comunicação:**
- Nunca usar "100% gratuito e sem planos pagos" (já removido da landing).
- "Grátis para sempre" refere-se sempre ao plano Free do serviço hospedado; "open source MIT" refere-se ao código.
- O Pro é apresentado como "ir além" (profundidade), nunca como "destravar o básico".

---

## 1. Clientes ideais (ICP)

### Segmento A — Universitário de graduação (Brasil) ✅ **RECOMENDADO PARA COMEÇAR**

| Dimensão | Descrição |
|---|---|
| Cargo/perfil | Estudante de graduação presencial ou EaD, 18–25 anos, geralmente no 1º–4º semestre, com **6+ matérias simultâneas**, período integral e frequentemente estágio/emprego |
| Tamanho | Individual (venda B2C) |
| Contexto de uso | Conciliar grade de aulas (o app tem campo literal de "sala", "bloco" e "professor"), tarefas com data de entrega, provas, e pouco tempo de estudo; usa o celular nos intervalos e o PC à noite |
| Sinais de prontos para comprar | Procura "como estudar"/"pomodoro"/"técnica de estudo"; já tem semana de provas acumulada; testou Forest, Focus To-Do, Notion ou planilha e abandonou; segue contas de "study tok"/estudos no Instagram e TikTok |
| Disposição a pagar | Baixa individualmente — monetização via freemium + recursos sociais premium (ver plano) |

**Por que começar por aqui:** o produto **já foi desenhado para essa rotina** — o quadro de horários presencial com sala/bloco/professor e a combinação pomodoro + matérias + tarefas + gamificação cobrem exatamente o semestre do universitário brasileiro. Além disso, as features sociais (amigos, clubes, ligas) criam um **loop viral de turma**: um aluno convida os colegas para competir por XP. Volume de mercado é o maior dos três segmentos. É o segmento com melhor *product-market fit* para o produto atual, sem precisar construir nada novo para vender a primeira versão.

### Segmento B — Vestibulando (ENEM / FUVEST / pré-vestibular)

| Dimensão | Descrição |
|---|---|
| Cargo/perfil | Estudante do ensino médio ou cursinho pré-vestibular, 16–19 anos, em preparação intensiva com prazo fixo (prova anual) |
| Tamanho | Individual; poder de compra muitas vezes via pais/responsáveis |
| Contexto de uso | Rotina de matérias pesadas, simulados, contagem regressiva para a prova; decisão de compra influenciada pela família |
| Sinais de prontos para comprar | Está em cursinho, faz plano de estudos manual, conta dias para o ENEM/FUVEST, segue canais de correção de redação e cronogramas de estudos |
| Disposição a pagar | Média (família costuma aceitar investimento pequeno na aprovação) — porém **sazonal** (pico antes da prova) |

### Segmento C — Concurseiro (concursos públicos)

| Dimensão | Descrição |
|---|---|
| Cargo/perfil | Adulto 22–40 anos, empregado ou estudando em tempo integral para concurso; jornada longa (meses a anos) |
| Tamanho | Individual |
| Contexto de uso | Muitas matérias com edital, ciclo longo, necessidade de **medição de horas e consistência**; já paga caro em cursinhos e materiais |
| Sinais de prontos para comprar | Já investe em cursos (assinatura de cursinho), usa planilhas de horas de estudo, acompanha editais |
| Disposição a pagar | **A mais alta dos três** — é o segmento que paga para sustentar o hábito de estudar |

**Por que não começar por aqui:** o app foi construído em torno da **grade universitária** (sala/bloco/professor, semestre), e o concurseiro precisa de recursos de ciclo longo (metas semanais, relatórios, sugestão de plano — ainda **«a validar»**/não implementados). Dá para vendê-lo depois com 2–3 features; hoje o fit é menor.

**Expansão B2B (futura, não para agora):** cursinhos e faculdades que querem medir/motivar a rotina de estudo dos alunos. **«a validar»** — hoje os clubes são entre pares; não existe painel de professor/instituição nem cobrança por licença.

---

## 2. Dor e trabalho a ser feito (JTBD)

**JTBD principal** (declaração funcional + emocional):
> "Quando estou no meio do semestre com várias matérias e prazos chegando, quero **organizar o que estudar a cada dia e me manter na rotina**, para passar nas matérias sem sofrer no fim do período."

**Trabalhos menores que o produto atende:**
- "Quero saber **quanto eu realmente estudo**" (as pessoas superestimam o tempo de foco — o registro de sessões e o analytics respondem).
- "Quero **não esquecer prazos e provas**" (tarefas com data de entrega + quadro de horários).
- "Quero **começar a estudar** mesmo sem motivação" (timer Pomodoro + missões diárias + streak empurram a primeira ação).
- "Quero **sentir progresso**" (XP, nível, conquistas — progresso que planilha não dá).

**O que acontece se não resolver:**
- Noite de véspera, "crumpir" (estudar tudo na última hora), reprovação, trancamento de semestre, perda de bolsa/PROUNI, atraso na formatura, ansiedade e culpa recorrentes, e em casos longos, desistência do curso. **«a validar»** — consequência plausível, não mensurada.

**Como resolve hoje (alternativas reais):**
| Alternativa | O que cobre | O que não cobre |
|---|---|---|
| Caderno / agenda de papel | Organização | Não registra tempo, não mede, não motiva |
| Planilha (Excel/Sheets) | Organização + horas | Fricção alta de preencher, zero motivação, sem mobile bom |
| Google Calendar / Notion | Agenda e notas | Não gamifica, não foca no estudo, depende de montagem própria |
| Apps de pomodoro (Forest, Focus To-Do, Tide) | Foco em sessão | Não enxergam o semestre inteiro (matérias, prazos, horas por área) |
| Apps de gamificação (Duolingo — só idioma) | Consistência | Não servem para matérias da faculdade |
| **"Não fazer nada"** | — | Improviso e estudo de véspera; é o concorrente mais frequente |

---

## 3. Diferenciais verificáveis

**Só o que o produto faz de fato e pode ser comprovado (todos checados na UI pública / código):**

1. **Timer Pomodoro com meta por tarefa + som ambiente + descanso automático** — vai além do "timer simples": vincula a sessão a uma área/tarefa e contabiliza pomodoros da meta.
2. **Gamificação alimentada pelos dados reais de estudo** — XP por minutos estudados e tarefas concluídas; coins por pomodoro; streak por dias com atividade; freezes (proteção de streak comprável com coins); missões diárias; conquistas em 6 categorias; ligas com promoção/rebaixamento.
3. **Quadro de horários com sala, bloco e professor** para aulas presenciais — desenhado para a grade universitária brasileira real.
4. **Modo convidado + upgrade sem perda de dados** — usa em 1 minuto sem cadastro; o progresso vira conta real na mesma linha (token JWT com claim `guest:true` → upgrade).
5. **Camada social funcional** — amigos, ranking/ligas, clubes, feed de atividade.
6. **Analytics de estudo** — distribuição por área, 30 dias, tendência diária, melhor dia, por dia da semana, heatmap de atividade.
7. **Gratuito, sem anúncios, open source (MIT)** — código auditável no GitHub.
8. **Sem instalação** — roda no navegador (desktop e mobile), login Google ou email, verificação de email e recuperação de senha.
9. **Bilíngue PT/EN com 8 temas** — personalização de verdade.

**Para "a validar" (não comprovado):**
- Número de usuários ativos, retenção, taxa de conversão (qualquer métrica de adoção).
- Depoimentos, clientes pagantes, cases de aprovação (inexistentes até aqui).
- Integrações com outras ferramentas (nenhuma encontrada no código).
- App nativo iOS/Android (o produto é web; comportamento como PWA **«a validar»**).
- Afirmações de resultado ("estude 2x mais", "passe em menos tempo") — **não usar em marketing** sem dado.

---

## 4. Declaração de posicionamento

> Para **universitários brasileiros** que precisam conciliar muitas matérias, aulas presenciais, estágio e prazos — e que já tentaram se organizar sozinhos e não mantiveram a rotina —
> o **Cronograma** é um **plano de estudos gamificado (web)** que **organiza matérias, tarefas e horários e usa XP, streaks, missões diárias e competição entre amigos para manter a consistência de estudo**.
> Diferente de **planilhas e cadernos** (que não medem tempo nem motivam) e de **apps de pomodoro isolados** (que não enxergam o semestre inteiro), ele **junta organização, foco e motivação em um único lugar — grátis e open source**.

---

## 5. Proposta de valor

**Frase principal:**
> **"Organize o semestre, estude com foco e transforme consistência em jogo — num só lugar, de graça."**

**5 variações por ângulo:**

| Ângulo | Variação |
|---|---|
| Dor | "Chega de noite de prova em cima do prazo: o Cronograma te mostra o que estudar e quando — antes do desespero." |
| Resultado | "Passe o semestre sabendo exatamente quantas horas cada matéria te consumiu — e por que sua rotina funcionou (ou não)." |
| Velocidade | "Da primeira sessão de foco em menos de 1 minuto, sem criar conta — e quando quiser, o progresso vira conta salva." |
| Custo | "O que planilha + caderno + 4 apps separados tentam fazer, em um só lugar: grátis e sem anúncios." |
| Risco | "Consistência não é força de vontade, é hábito. O streak e as conquistas seguram você nos dias em que a motivação faltar." |

---

## 6. Mensagens-chave por persona e objeções

### Mensagens-chave

**Universitário (ICP principal):**
- "Sua grade de aula, suas matérias, seus prazos e seu foco num lugar só — e você ganha XP de verdade por estudar."
- "Competição leve com os amigos: clube, liga e ranking transformam estudar junto em jogo."
- "Você descobrirá quanto tempo *realmente* estuda — quase sempre menos do que acha."

**Vestibulando:**
- "Cada dia de estudo conta. Veja o que falta estudar e não deixe o streak morrer antes da prova."
- "Plano diário com missões: o que fazer hoje não é mistério."

**Concurseiro:**
- "Horas registradas, matérias organizadas e consistência medida — o que você estuda vira dado, não promessa."
- "Jornada longa exige ritmo: streak, metas e histórico mostram se você está avançando de verdade."

### 8 objeções prováveis + respostas honestas

1. **"Já uso planilha / Google Calendar."**
   *"Planilha organiza, mas não registra o tempo que você realmente estuda, não te mostra onde está atrasado e não te faz voltar amanhã. O Cronograma mede e motiva — que é o que falha na planilha."*

2. **"Não vou manter mais um app."**
   *"Não precisa. Você entra como convidado, faz um pomodoro em 1 minuto e sai. Se voltar, o progresso continua lá — e só vira conta quando você quiser."*

3. **"É grátis? Onde está o golpe?"**
   *"É grátis e open source (MIT) — o código está público no GitHub para qualquer um auditar. O Free é grátis para sempre; o Pro (R$ 20/mês) cobra recursos avançados de dados e produtividade para quem quer ir além."*

4. **"Gamificação é bobeira, preciso de resultado."**
   *"Justo. A gamificação é só o motor de consistência — o núcleo é organização de matérias, tarefas com prazo, pomodoro e analytics de horas. Se você não liga para XP, usa o resto."*

5. **"Minha rotina é bagunçada demais para um app."**
   *"O app não exige rotina perfeita — ele registra o que você consegue fazer e mostra onde o tempo foi parar. É para quem estuda nos buracos do dia, não para quem tem dia ideal."*

6. **"Não tem app nativo na loja."**
   *"Funciona no navegador de qualquer celular ou PC, sem instalar nada. Experiência instalável (PWA) é o próximo passo, mas o acesso é imediato hoje."*

7. **"Meus dados de estudo podem vazar."**
   *"Senha com hash, tokens JWT com revogação de sessão, login Google, verificação de email e recuperação de senha. E por ser open source, o tratamento de dados é auditável."*

8. **"Já uso Forest / Focus To-Do."**
   *"Eles resolvem o foco de uma sessão. O Cronograma faz isso **e** organiza o semestre: matérias, prazos, horas por área e competição com amigos. Uma peça em vez de quatro."*

---

## Suposições mantidas

- **Mercado-alvo:** Brasil (produto, conteúdo e contexto são pt-BR; EN também disponível).
- **Venda individual (B2C)**, não licenças institucionais nesta fase.
- **ICP:** universitário de graduação primeiro (seção 1); vestibulando e concurseiro nas fases seguintes.

As 3 perguntas do rascunho original foram respondidas em 14/11/2026 (ver "Decisões de negócio confirmadas"): precificação freemium com Pro a R$ 20/mês (+ futuro Ultra a R$ 50/mês), marketing 100% orgânico e reposicionamento da landing autorizado. O desdobramento operacional está em `marketing/plano-crescimento-organico.md`.

---

*Documento criado em 2026-11-14. Próximo passo sugerido: responder às 3 perguntas e, a partir daqui, desenhar o funil (landing → cadastro → ativação no 1º pomodoro → upsell Pro) e a campanha de conteúdo.*