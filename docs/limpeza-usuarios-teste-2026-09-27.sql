-- ============================================================================
-- Limpeza das contas de teste criadas no diagnóstico de 2026-09-27
-- Alvo: 27 usuários @example.com (ids 25..51) criados entre 20:03 e 20:10 UTC
--
-- CONFERIDO ANTES DE EXECUTAR:
--   * Os 27 @example.com do banco sao TODOS deste diagnostico
--     (nenhum @example.com pre-existente).
--   * Nenhuma FK aponta para users (0 restricoes found).
--   * areas/tasks/sessoes com user_id 25..51: 0 linhas.
--
-- Rodar em transacao para poder reverter com ROLLBACK.
-- ============================================================================

BEGIN;

-- 1) Backup do que sera removido (opcional, so para conferencia)
-- SELECT id, email, created_at FROM users
--  WHERE email LIKE '%@example.com' ORDER BY created_at;

-- 2) Remocao. O filtro por created_at evita apagar contas reais caso
--    alguem crie um @example.com legitimo no futuro.
DELETE FROM users
 WHERE email LIKE '%@example.com'
   AND created_at >= '2026-09-27T19:50'
RETURNING id, email;

-- 3) Conferir que sobrou apenas o que existia antes do diagnostico
SELECT count(*) AS restantes_example_com FROM users WHERE email LIKE '%@example.com';
SELECT count(*) AS total_users FROM users;

COMMIT;
-- Se algo parecer errado, trocar COMMIT por ROLLBACK e rodar de novo.
