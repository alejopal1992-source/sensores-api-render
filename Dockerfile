FROM python:3.10-slim

# Variables de entorno
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Dependencias del sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential git && \
    rm -rf /var/lib/apt/lists/*

# Usuario no-root (seguridad)
RUN useradd -m -d /home/appuser -s /bin/bash appuser

WORKDIR /app

# Instalar dependencias Python (capa cacheada)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Crear carpetas de runtime
RUN mkdir -p /app/data /app/reports /app/models && \
    chown -R appuser:appuser /app

# Copiar código fuente
COPY --chown=appuser:appuser . /app

# Pre-entrenar modelo durante el build
USER appuser
RUN python train_model.py

# Puerto dinámico para Render
ENV PORT=10000
EXPOSE $PORT

# Comando de arranque (formato shell para resolver $PORT)
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
