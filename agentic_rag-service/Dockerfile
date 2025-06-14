# Especificar plataforma para Cloud Run
FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-descargar el modelo de embeddings para evitar descarga en runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copiar archivos del proyecto existentes
COPY main.py .

# Crear directorios necesarios
RUN mkdir -p /app/data /app/knowledge_base /app/vector_db /app/logs

# Variables de entorno para Cloud Run
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production
ENV USE_EMBEDDED_CHROMA=true
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Cloud Run ejecuta en el puerto 8080
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Comando para Cloud Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]