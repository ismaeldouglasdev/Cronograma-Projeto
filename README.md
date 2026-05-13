
<p align="center">
  <h1 align="center">📅 Cronograma de Estudos Gamificado</h1>
  <p align="center">Sistema full-stack com mecânicas de gamificação para melhorar hábitos de estudo e produtividade</p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript">
  <img src="https://img.shields.io/badge/GPL--3.0-blue?style=for-the-badge" alt="License">
</p>

---

## 📋 Sobre o Projeto

Sistema full-stack de cronograma de estudos com **gamificação** (níveis, progressão, consistência) para aumentar a produtividade nos estudos. Foco em comportamento do usuário, retenção e disciplina.

### 🎯 Funcionalidades

- 🎮 **Mecânicas de gamificação** — Níveis, progressão, recompensas e consistência
- 📊 **Acompanhamento visual** — Gráficos e estatísticas de desempenho
- 🏆 **Sistema de conquistas** — Medalhas e ícones de progresso
- 🔥 **Sequência de dias** — Streak de consistência para manter o hábito
- 📱 **Interface responsiva** — Acesso de qualquer dispositivo

---

## 🚀 Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| **Backend** | Python + Flask |
| **Banco** | PostgreSQL (produção) / SQLite (desenvolvimento) |
| **Frontend** | HTML, CSS, JavaScript |
| **Infra** | Docker, Docker Compose |
| **Deploy** | Heroku (Procfile + runtime.txt) |

---

## 🛠️ Como Rodar

### Com Docker (recomendado)

```bash
docker-compose up --build
```

### Manualmente

```bash
# Instalar dependências
pip install -r cronograma/requirements.txt

# Configurar banco
cd cronograma
python migrate_to_pg.py

# Rodar
python app/main.py
```

> No Windows, use `iniciar_cronograma.bat` para iniciar rapidamente.

---

## 🏗️ Estrutura

```
Cronograma-Projeto/
├── cronograma/
│   ├── app/                  # Código principal da aplicação
│   ├── static/               # Arquivos estáticos (CSS, JS, imagens)
│   ├── main.py               # Ponto de entrada
│   ├── requirements.txt      # Dependências Python
│   ├── Dockerfile            # Build Docker
│   └── docker-compose.yml    # Orquestração de serviços
├── icon_images/              # Ícones do sistema de gamificação
├── AGENTS.md                 # Documentação do projeto
├── LICENSE                   # GPL-3.0
└── README.md
```

---

## 📄 Licença

Este projeto é licenciado sob a [GNU General Public License v3.0](LICENSE).

---

<p align="center">
  Feito com ❤️ por <a href="https://github.com/ismaeldouglasdev">Ismael Douglas</a>
</p>
