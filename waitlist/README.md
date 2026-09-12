# Cronograma Pro — Lista de Espera

Landing page para validar demanda do Cronograma Pro (versão SaaS).

## Setup do Formspree

1. Acesse [formspree.io](https://formspree.io/) e crie uma conta gratuita
2. Crie um novo form e copie o ID (algo como `xrgkzbnp`)
3. No `index.html`, substitua `YOUR_FORM_ID` pelo seu ID real:
   ```
   https://formspree.io/f/xrgkzbnp  ← troque aqui
   ```
4. Na aba "Emails" do formspree, configure seu email de notificação

## Deploy

### Opção 1: GitHub Pages (recomendado para zero custo)
```bash
git init
git add waitlist/
git commit -m "feat: landing page lista de espera"
gh repo create cronograma-waitlist --public --source=. --push
# Ativar GitHub Pages: Settings → Pages → branch main → /waitlist
# URL: https://seu-usuario.github.io/cronograma-waitlist/
```

### Opção 2: Render Static Site
```bash
# Criar render.yaml na raiz do waitlist/
# Deploy automático via GitHub
```

### Opção 3: Servir localmente
```bash
cd waitlist/
python3 -m http.server 8000
# Abrir http://localhost:8000
```

### Opção 4: Adicionar ao app existente
Copie `index.html` para a pasta `static/` do FastAPI ou mova para o diretório de arquivos estáticos do Render.

## Personalização

- **Cor**: edite as variáveis CSS em `:root`
- **Contador social**: troque `500+` pelo número real (ou adicione um counter no Formspree)
- **Links**: atualize footer com redes sociais reais
- **OG tags**: ajuste `og:image` com um banner de 1200x630px

## Métricas

Após deploy, monitore:
- **Conversão**: visitantes / inscrições no form
- **Fonte de tráfego**: adicione UTM params no link (`?utm_source=instagram&utm_campaign=waitlist`)
- **Feedback**: crie um campo "Como você nos encontrou?" no Formspree