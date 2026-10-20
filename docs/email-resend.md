# Fluxo de e-mail (Resend)

## Configuração
- Provedor: [Resend](https://resend.com/) via API HTTP com `httpx`
- Variáveis de ambiente (Render + `.env` local):
  - `RESEND_API_KEY`
  - `EMAIL_FROM` (ex: `verificacao@ismaeltech.com` ou `onboarding@resend.dev` se domínio não verificado)
- Implementação: `cronograma/app/services/email_service.py`

## Fluxos

### Verificação de e-mail
1. Usuário registra em `/auth/register`
2. Sistema envia e-mail via Resend com link `APP_URL/auth/verify-email?token=...`
3. Usuário clica no link → `/auth/verify-email` valida token e ativa `is_verified`
4. Fallback: em caso de falha no envio, UI pode exibir token manualmente

### Esqueci minha senha (password reset)
1. `POST /auth/forgot-password` com email → sempre retorna 200 (anti-enumeração)
2. Token gerado, hash SHA-256 armazenado em `password_reset_tokens` (expiração 30 min, uso único)
3. E-mail enviado com link `APP_URL/auth/reset-password?token=...`
4. `POST /auth/reset-password` valida token (não usado, não expirado) → atualiza `password_hash` (bcrypt) → marca `used_at`
5. Rate limit aplicado por IP/e-mail

## Segurança
- Token nunca armazenado em claro (apenas hash)
- Resposta genérica em forgot-password
- Single-use tokens
- Expiração 30 minutos
- Rate limiting
