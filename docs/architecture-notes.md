# Notas de Arquitetura

## JWT stateless - dívida técnica
- Autenticação usa JWT stateless (`python-jose`). Tokens não são revogados server-side.
- Ao resetar senha via `/auth/reset-password`, **sessões JWT existentes não são invalidadas**.
- Impacto: tokens antigos permanecem válidos até expiração natural.
- Mitigação futura: implementar token blocklist (Redis) ou rotação por versão de token por usuário. 
- Status: aceito para este release (abordagem incremental conforme plano).
