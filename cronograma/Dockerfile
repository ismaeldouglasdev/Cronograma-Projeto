# ============================================
# Cronograma - Dockerfile
# Melhor prática: Multi-stage build para produção
# ============================================

# ---------------------------------------------------------
# Stage 1: Builder
# ---------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar ambiente virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements.txt


# ---------------------------------------------------------
# Stage 2: Production
# ---------------------------------------------------------
FROM python:3.11-slim AS production

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PORT=8000

WORKDIR /app

# Criar usuário não-root para segurança
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 appuser

# Copiar ambiente virtual do builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar código da aplicação
COPY --chown=appuser:appgroup app/ ./app/

# Expor porta
EXPOSE 8000

# Mudar para usuário não-root
USER appuser

# ---------------------------------------------------------
# Stage 3: Development (opcional)
# ---------------------------------------------------------
FROM production AS development

# Sem dependências extras - apenas usa o que já está instalado

# Iniciar com reload para development
CMD ["/opt/venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
