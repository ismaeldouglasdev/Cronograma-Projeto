-- Migration SQL from SQLite to PostgreSQL
-- Run this in your PostgreSQL database on Render

-- USERS
INSERT INTO users (id, email, password_hash, created_at, is_verified, verification_token) VALUES (1, 'y2kgif@gmail.com', 'a643c144aa6b6d66a73c7454b576f76f1b97d7c6858674dfb808a3870cfd0b54', '2026-02-19T04:12:13.267797', true, NULL);
INSERT INTO users (id, email, password_hash, created_at, is_verified, verification_token) VALUES (2, 'teste@gmail.com', '4f5e87b86aa07259fdb452eb03d36661933443471e23c496a9e7d78ac1332c8b', '2026-02-19T04:55:11.727469', false, NULL);
INSERT INTO users (id, email, password_hash, created_at, is_verified, verification_token) VALUES (3, '1212@gmail.com', 'cbfad02f9ed2a8d1e08d8f74f5303e9eb93637d47f82ab6f1c15871cf8dd0481', '2026-02-22T19:22:27.002187', false, NULL);
INSERT INTO users (id, email, password_hash, created_at, is_verified, verification_token) VALUES (4, 'ashuash@gmail.com', '20f2780aa4c618bf35a1b2f26ef9928aa080462fb70fb8799e9d74d938c7e8fa', '2026-02-23T14:49:39.510827', false, NULL);
INSERT INTO users (id, email, password_hash, created_at, is_verified, verification_token) VALUES (5, 'ygwdw@gmail.com', '75744a2b7e24f94b1899af563e4f9c6c0cf2d8bbf4762fe203d2903ceee82751', '2026-02-24T22:33:43.216669', false, '20ea41e0-03f4-4cd9-b01e-a675951e3fbf');

-- AREAS
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (3, 'Programação Web', '#00ff44', NULL, 'presencial', 'terca', '19:00 - 20:40', 'Laboratório 4', ' ', 'Andre', 'Disciplinas Híbridas HAMI');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (4, 'Desenvolvimento Mobile ', '#0008ff', NULL, 'presencial', 'sexta', '21:00 - 22:40', '203', 'E', 'Luiz', 'Disciplinas Híbridas HAMI');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (5, 'Projeto de Extensão II - Análise e Desenvolvimento de Sistemas', '#ff9100', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Disciplinas Projeto de Extensão');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (6, 'Programação e Desenvolvimento em Banco de Dados', '#c8ff00', NULL, 'presencial', 'quinta', '19:00 - 21:50', '104', 'E', 'Andre', 'Aula Modelo Institucional');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (7, 'Infraestrutura Ágil ', '#ee00ff', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Disciplinas Interativas KLS 2.0');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (8, 'Desenvolvimento em JavaScript ', '#ff0000', NULL, 'presencial', 'quarta', '21:00 - 22:40', 'Laboratório 1', ' ', 'Marcel', 'Aula Modelo Institucional');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (9, 'Qualidade e Automação de Testes', '#00bfff', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Disciplinas Interativas (DI) - WL');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (10, 'Competências para a Vida', '#64f2a8', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Cursos Complementares');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (11, 'Ciências Biológicas', '#5781ff', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Cursos Complementares');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (12, 'Matemática', '#d3f264', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Cursos Complementares');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (13, 'Português', '#f1376f', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Cursos Complementares');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (14, 'Processo Seletivo', '#64eff2', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Cursos Complementares');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (15, 'Análise de Dados com Python', '#ffbb00', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Trilha de Carreira');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (16, 'Análise de Investimentos e Fontes de Financiamento', '#2675a6', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Trilha de Carreira');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (17, 'Língua Espanhola I', '#8af264', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Trilha de Carreira');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (18, 'Lígua Espanhola II', '#8af264', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Trilha de Carreira');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (19, 'Língua Inglesa I', '#f26464', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Trilha de Carreira');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (20, 'Língua Inglesa III', '#f26464', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Trilha de Carreira');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (21, 'Língua Inglesa IV', '#f26464', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Trilha de Carreira');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (22, 'Matemática Financeira', '#fff700', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Trilha de Carreira');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (23, 'Noções de Atuária', '#fff700', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Trilha de Carreira');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (24, 'Produção de Conteúdo', '#bb00ff', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Trilha de Carreira');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (25, 'Wordpress na Prática', '#35367e', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Trilha de Carreira');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (26, 'freeCodeCamp: Python', '#ffa200', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Estudos Pessoais');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (27, 'Engenharia Backend – Segurança e Autenticação', '#00ff33', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Estudos Pessoais');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (28, 'Projeto: Cronograma', '#27d39f', NULL, 'online', NULL, NULL, NULL, NULL, NULL, 'Estudos Pessoais');
INSERT INTO areas (id, nome, cor, ordem, tipo, dia_semana, horario, sala, bloco, professor, subcategoria) VALUES (29, 'teste', '#6366f1', NULL, 'online', NULL, NULL, NULL, NULL, NULL, NULL);

-- TASKS
INSERT INTO tasks (id, area_id, titulo, descricao, data_entrega, concluida, duracao_minutos, prioridade, meta_pomodoros, pomodoros_concluidos) VALUES (1, 10, 'Certificado: Competências para a Vida', 'Fazer os 3 módulos e a avaliação, e depois emitir o certificado de Competências para a Vida.', '2026-02-23', true, 30, 3, NULL, 0);
INSERT INTO tasks (id, area_id, titulo, descricao, data_entrega, concluida, duracao_minutos, prioridade, meta_pomodoros, pomodoros_concluidos) VALUES (2, 14, 'Certificado: Processo Seletivo', 'Fazer os 4 módulos de Processo Seletivo e depois emitir o Certificado.', '2026-02-27', false, 1, 3, NULL, 2);
INSERT INTO tasks (id, area_id, titulo, descricao, data_entrega, concluida, duracao_minutos, prioridade, meta_pomodoros, pomodoros_concluidos) VALUES (3, 5, 'Realizar e entregar o Projeto de Extensão', 'Completar os 3 módulos da disciplina no AVA, realizar o projeto, entregar o relatório final e ser aprovado com pelo menos 60 pontos. Se for retornado, ir entregando novamente com melhorias até atingir a meta de pontos.', '2026-03-09', false, 1, 3, NULL, 0);
INSERT INTO tasks (id, area_id, titulo, descricao, data_entrega, concluida, duracao_minutos, prioridade, meta_pomodoros, pomodoros_concluidos) VALUES (4, 27, 'Fundamentos de Autenticação em Sistemas Web', 'Estudos de fundamentos de autenticação em sistemas web usando JWT.', '2026-02-20', true, 1, 2, 5, 2);
INSERT INTO tasks (id, area_id, titulo, descricao, data_entrega, concluida, duracao_minutos, prioridade, meta_pomodoros, pomodoros_concluidos) VALUES (5, 9, 'Atividade Discursiva', NULL, '2026-03-30', false, 1, 1, NULL, 0);
INSERT INTO tasks (id, area_id, titulo, descricao, data_entrega, concluida, duracao_minutos, prioridade, meta_pomodoros, pomodoros_concluidos) VALUES (6, 7, 'Atividade discursiva', NULL, '2026-03-30', false, 1, 1, NULL, 0);
INSERT INTO tasks (id, area_id, titulo, descricao, data_entrega, concluida, duracao_minutos, prioridade, meta_pomodoros, pomodoros_concluidos) VALUES (7, NULL, 'Período de prova de 1º bimestre', NULL, '2026-04-06', false, NULL, 3, NULL, 0);
INSERT INTO tasks (id, area_id, titulo, descricao, data_entrega, concluida, duracao_minutos, prioridade, meta_pomodoros, pomodoros_concluidos) VALUES (8, NULL, 'Período de prova de 2º bimestre', NULL, '2026-06-01', false, NULL, 1, NULL, 0);
INSERT INTO tasks (id, area_id, titulo, descricao, data_entrega, concluida, duracao_minutos, prioridade, meta_pomodoros, pomodoros_concluidos) VALUES (9, NULL, 'Período de prova da Disciplina Interativa:', NULL, '2026-06-01', false, NULL, 1, NULL, 0);
INSERT INTO tasks (id, area_id, titulo, descricao, data_entrega, concluida, duracao_minutos, prioridade, meta_pomodoros, pomodoros_concluidos) VALUES (10, 3, 'Atividade feita em sala de aula', 'Criação de página HTML simples.', '2026-02-24', true, 60, 2, NULL, 0);

-- SESSOES
INSERT INTO sessoes (id, area_id, duracao_minutos, data, task_id) VALUES (1, 26, 32, '2026-02-16', NULL);
INSERT INTO sessoes (id, area_id, duracao_minutos, data, task_id) VALUES (2, 10, 30, '2026-02-16', NULL);
INSERT INTO sessoes (id, area_id, duracao_minutos, data, task_id) VALUES (3, 27, 50, '2026-02-17', NULL);
INSERT INTO sessoes (id, area_id, duracao_minutos, data, task_id) VALUES (4, 10, 19, '2026-02-17', NULL);
INSERT INTO sessoes (id, area_id, duracao_minutos, data, task_id) VALUES (5, 10, 25, '2026-02-17', NULL);
INSERT INTO sessoes (id, area_id, duracao_minutos, data, task_id) VALUES (6, 10, 30, '2026-02-18', 1);
INSERT INTO sessoes (id, area_id, duracao_minutos, data, task_id) VALUES (7, 27, 15, '2026-02-20', NULL);
INSERT INTO sessoes (id, area_id, duracao_minutos, data, task_id) VALUES (8, 27, 1, '2026-02-21', 4);
INSERT INTO sessoes (id, area_id, duracao_minutos, data, task_id) VALUES (12, 3, 60, '2026-02-24', 10);
INSERT INTO sessoes (id, area_id, duracao_minutos, data, task_id) VALUES (13, 8, 25, '2026-02-25', NULL);
INSERT INTO sessoes (id, area_id, duracao_minutos, data, task_id) VALUES (14, 8, 17, '2026-02-25', NULL);
INSERT INTO sessoes (id, area_id, duracao_minutos, data, task_id) VALUES (15, 8, 12, '2026-02-25', NULL);
