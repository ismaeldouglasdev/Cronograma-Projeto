# ============================================
# Cronograma - Dockerfile (SQLite local)
# ============================================

FROM python:3.11-slim

WORKDIR /app

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY app/ ./app/

# Copiar banco de dados pré-populado para o local correto
COPY app/cronograma.db .

# Expor porta
EXPOSE 8000

# Iniciar servidor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
