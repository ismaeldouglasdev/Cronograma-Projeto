# Notas de Arquitetura

## JWT stateless - revogação por versão de token

Autenticação continua stateless (`python-jose`), mas cada usuário tem
`users.token_version`. Todo access/refresh token carrega o claim `ver`:

- `get_current_user` consulta o usuário e rejeita o token quando
  `ver != users.token_version` (ou quando o usuário foi excluído).
- `POST /auth/reset-password` incrementa `token_version` → access e refresh
  tokens emitidos antes do reset deixam de valer imediatamente.
- `POST /auth/logout-all` incrementa `token_version` e limpa os cookies →
  encerra todas as sessões, inclusive a atual.
- Tokens emitidos antes deste campo (sem claim `ver`) são tratados como
  versão 0 e continuam válidos até o primeiro reset/logout global.

O custo é uma consulta ao usuário por requisição autenticada. Não há
blocklist em Redis: a versão por usuário resolve revogação sem infra nova.
