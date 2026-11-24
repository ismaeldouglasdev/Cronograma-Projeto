# Plano de Crescimento Orgânico — Ritmo Exato

> Como vender o SaaS com marketing 100% orgânico. Complementa `marketing/posicionamento.md` (o "o quê" e "para quem").
> Data: 2026-11-14 · **Regra:** nada de números, clientes ou features inventados; o que não existe está marcado **«a validar»**.
> Base: app atual (verificado), `waitlist/CONTENT-STRATEGY.md`, `waitlist/APP-IMPROVEMENTS.md`.

---

## 1. Modelo de receita (confirmado)

| Tier | Preço | Papel no funil |
|---|---|---|
| **Free** | R$ 0 (para sempre) | Porta de entrada. Chama o usuário para dentro, ativa no 1º pomodoro, sustenta o boca a boca |
| **Pro** | **R$ 20/mês** | Upgrade de valor: dados profundos, produtividade e personalização |
| **Ultra** | R$ 50/mês (futuro) | Público muito engajado / jornadas longas (concurseiros). **«a validar»**: data e recursos |

### O que cada tier entrega (honesto — só cobrar o que existir)

| Recurso | Free (hoje) | Pro (R$ 20) | Status da feature |
|---|---|---|---|
| Matérias, tarefas, prazos, prioridades | ✅ | ✅ | construído |
| Pomodoro configurável + som ambiente | ✅ | ✅ | construído |
| Sessões + analytics de 30 dias | ✅ | ✅ | construído |
| Gamificação (XP, coins, streak, conquistas, missões, ligas, clubes, amigos) | ✅ | ✅ | construído |
| Quadro de horários, temas, PT/EN | ✅ | ✅ | construído |
| Heatmap de atividade completo (365 dias) | 30 dias | 365 dias | **«a validar»** (roadmap) |
| Analytics profundo (90+ dias, insights, comparações) | 7–30 dias | completo | **«a validar»** (roadmap) |
| Missões premium + recompensas extras | 3/dia | ilimitadas | **«a validar»** (roadmap) |
| Metas semanais por matéria | 1 | ilimitadas | **«a validar»** (roadmap) |
| Subtarefas / checklist | 3/tarefa | ilimitadas | **«a validar»** (roadmap) |
| Relatório semanal automático | básico | completo | **«a validar»** (roadmap) |
| Sons ambiente e temas exclusivos | 2 sons | biblioteca completa | **«a validar»** (roadmap) |
| Exportar cards de progresso (redes sociais) | ✅ grátis | ✅ grátis | **«a validar»** (roadmap) |
| Turmas privadas, desafios em grupo, sugestão inteligente, modo prova | — | — | **Ultra** (futuro) |

> **Consequência prática:** enquanto as features Pro não existem, **não se cobra o Pro**. Primeiro se implementa a Fase 1 de quick wins do `waitlist/APP-IMPROVEMENTS.md` (heatmap 365d, analytics, missões premium, metas semanais, subtarefas, relatório — todos de 1–3 dias de esforço estimado). Depois se abre o checkout.

---

## 2. Funil de conversão

```
TOPO (orgânico)          MEIO (conversão)                 FUNDO (ativação + receita)
conteúdo social  ──►   landing reposicionada   ──►   1º pomodoro (aha moment)
SEO (blog + repo)      cadastro (Google/email)          missões diárias + streak
GitHub/open source     OU modo convidado                upsell Pro (gatilhos)
boca a boca (liga)     (zero fricção)                   reengajamento (email)
```

### TOPO — aquisição (100% orgânico)

1. **Conteúdo social (IG + TikTok + X).** A estratégia de 2 semanas já está pronta em `waitlist/CONTENT-STRATEGY.md`. **Ajuste necessário:** o CTA dos posts deve apontar para o app (`ritmo-exato.onrender.com/app`), não para a waitlist morta. Pilares que mais vendem aqui: gamificação (tela do app como prova) e rotina real.
2. **SEO via blog próprio.** O usuário tem um blog bilíngue ativo (Hugo, ismaeltech.com) com tráfego e postagem automática diária. Propor posts-alvo: "como montar um cronograma de estudos", "app de estudos com pomodoro", "técnica pomodoro adaptada", com link natural para o produto. **«a validar»**: posição atual do blog no Google.
3. **GitHub / open source.** O repo público (`ismaeldouglasdev/Cronograma-Projeto`, MIT) é um canal: estudante de TI encontra, usa, estrela e indica. Manter README com screenshot e link ao vivo; abrir issues boas para contribuidores = engajamento de comunidade (e conteúdo).
4. **Boca a boca por loop viral (já construído).** Amigos, clubes e ligas fazem o convite competitivo: "entra na minha liga, bora ver quem estuda mais". É o motor de crescimento mais barato e já funciona no produto. Pedir o convite no momento em que o usuário sobe de liga/streak.

### MEIO — conversão

- **Landing reposicionada** (copy pronta na seção 7) — mensagem de valor/resultado, com Free grátis para sempre + Pro "em breve".
- **Cadastro sem fricção:** Google OAuth em 1 clique ou **modo convidado** (usa na hora, vira conta quando quiser). CTA principal da landing: "Experimentar sem cadastro".
- **Uma conta por dispositivo:** os dados de convidado sobrevivem ao upgrade (verificado no produto).

### FUNDO — ativação e monetização

- **Aha moment:** completar o **1º pomodoro** na primeira visita (missões diárias e a tela de foco empurram para isso).
- **Retenção:** streak, freezes, missões diárias e notificação de "streak em risco" — o produto já tem Resend (email) integrado; usar para reengajamento (D7/D30 e streak em risco). **«a validar»**: envio de email transacional já funciona (verificação/reset); campanhas de reengajamento precisam ser construídas.
- **Upsell Pro:** mostrar o valor antes de pedir dinheiro (ver gatilhos abaixo).

---

## 3. Gatilhos de upsell (momentos de pedir o Pro)

Só pedir o upgrade quando o usuário esbarrou no limite ou viu o valor:

1. **Heatmap chegando no limite dos 30 dias** — "Seu histórico anual, análises completas e comparações com semanas anteriores no Pro."
2. **Streak ≥ 7 dias** — usuário já provou consistência; "Proteja e aprofunde seu ritmo".
3. **Semana de provas** — dados de preparação viram urgência ("veja onde você está atrasado por matéria").
4. **Missões premium bloqueadas** no fluxo diário.
5. **Meta semanal por matéria** — primeira vez que o usuário define meta, mostra a profundidade do Pro.
6. **Relatório semanal** — o card de "sua semana em números" termina com upgrade.

Formato honesto: modal de upgrade com lista concreta do que desbloqueia + botão, sem escadinha de manipulação. Preço âncora: R$ 20/mês é ~o preço de um lanche mensal; custo de oportunidade comparado a cursinho/monitoria — comparações apenas com valores públicos.

---

## 4. Canais orgânicos — prioridade

| # | Canal | Esforço | Papel | Quando |
|---|---|---|---|---|
| 1 | Loop social (ligas/clubes) | baixo | crescimento interno | **agora** (já construído) |
| 2 | Conteúdo IG/TikTok/X | médio | aquisição | agora (estratégia pronta, ajustar CTA) |
| 3 | Blog/SEO (ismaeltech.com) | médio | aquisição perene | semana 2–3 |
| 4 | GitHub/open source | baixo | marca + comunidade | contínuo |
| 5 | Email de reengajamento (Resend) | médio | retenção | após instrumentar funil |

---

## 5. Métricas (metas propostas — **«a validar»** com dados reais)

| Métrica | Meta sugerida | Medição |
|---|---|---|
| Ativação: contas que completam 1º pomodoro | ≥ 50% das contas novas | evento no backend |
| Retenção D7 / D30 | D7 ≥ 40%, D30 ≥ 25% | sessões ativas por conta |
| Conversão convidado → conta | ≥ 30% dos convidados que fizeram 1 pomodoro | evento `/auth/upgrade` |
| Conversão Free → Pro | benchmark de mercado 4–9% (fonte: pesquisa citada no APP-IMPROVEMENTS.md) | checkout |
| Convidados por usuário ativo (K-fator) | ≥ 0.3 no trimestre | eventos de convite |

> Nenhuma métrica é número de clientes inventado — são metas a calibrar com as primeiras semanas de dado real.

---

## 6. Plano de 30 dias (100% orgânico)

**Semana 1 — Fundação de mensagem**
- [ ] Aplicar a nova copy da landing (seção 7): headline de valor, FAQ com Free/Pro, CTA "Experimentar sem cadastro".
- [ ] Publicar 3–5 conteúdos seguindo a `CONTENT-STRATEGY.md` com CTA para `/app`.
- [ ] Conferir que o caminho convidado → conta → 1º pomodoro funciona sem atrito (testar de ponta a ponta).

**Semana 2 — Aquisição + retenção**
- [ ] 2 posts de SEO no blog com link para o produto (termos: cronograma de estudos, pomodoro, app de estudos).
- [ ] Lançar 1 desafio orgânico (#Desafio7DiasDeEstudo — mecânica já descrita na CONTENT-STRATEGY).
- [ ] Iniciar construção das quick wins do Pro (heatmap 365d e analytics são os de maior impacto por esforço).

**Semana 3 — Instrumentação**
- [ ] Registrar eventos mínimos: cadastro, convidado, 1º pomodoro, streak, upgrade.
- [ ] Email de reengajamento D7/D30 via Resend (infra já existe).
- [ ] Decidir o gate Pro v1: quais features entram no primeiro corte pago.

**Semana 4 — Revisão e dobra**
- [ ] Ler métricas reais da Semana 1–3; calibrar metas.
- [ ] Dobrar o pilar de conteúdo com melhor desempenho (conteúdo que gera cadastro, não só views).
- [ ] Abrir o Pro (R$ 20/mês) **somente quando o gate v1 estiver construído**.

---

## 7. Copy da landing (proposta pronta para aplicar)

> Substitui o "100% grátis • Open Source" por mensagem de valor. O plano Pro aparece como "em breve" até as features existirem (regra de confiança).

**Headline:**
> Seus estudos, com disciplina — e prova disso.

**Subheadline:**
> Organize matérias e prazos, estude com Pomodoro e evolua com XP, conquistas e competição com amigos. Grátis para sempre. Sem anúncios.

**Bloco "Como funciona"** (manter os 3 passos atuais: Organize → Estude com foco → Evolua).

**Bloco "Tudo para sua rotina de estudos"** (manter cards atuais).

**Novo bloco de preço (no rodapé):**
```
Free — R$ 0 para sempre
  Matérias, tarefas, prazos e quadro de horários
  Pomodoro com som ambiente
  Gamificação completa (XP, streak, conquistas, ligas, clubes)
  Analytics de 30 dias

Pro — R$ 20/mês · em breve
  Histórico completo (365 dias) e analytics profundos
  Missões premium, metas semanais e relatório semanal
  Subtarefas ilimitadas, sons e temas exclusivos
```

**FAQ (atualizar respostas):**
- "O Ritmo Exato é gratuito?" → *"Sim — o plano Free é grátis para sempre e sem anúncios. Existe o Pro (R$ 20/mês), em fase final de preparação, com recursos avançados de dados e produtividade."*
- "Preciso criar conta?" → *"Não para começar: use o modo convidado e, quando quiser salvar seu progresso, crie a conta em 1 clique (Google) — nada se perde."*
- "Como funciona a gamificação?" → manter resposta atual.
- "O que é o streak?" → manter resposta atual.
- "O código é aberto?" → *"Sim, MIT no GitHub — qualquer pessoa pode auditar."*

---

## 8. O que NÃO fazer (regras de honestidade)

- Não anunciar features Pro que ainda não existem como se estivessem prontas (a landing fala "em breve").
- Não inventar prova social ("500+ usuários", depoimentos) — mostrar a tela real do app é a prova.
- Não prometer resultado acadêmico ("passe na prova", "estude 2x mais") sem dado.
- Não fazer cold outreach em massa — o objetivo é o funil orgânico; sem verba, alcance se compra com conteúdo e produto, não com spam.

---

*Documento criado em 2026-11-14. Próximo passo: aplicar a seção 7 na landing (arquivo estático do app) — exige edição no código e novo deploy no Render.*