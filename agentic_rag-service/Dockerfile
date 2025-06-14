FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos del proyecto
COPY main.py .

# Crear directorios necesarios
RUN mkdir -p /app/data /app/knowledge_base /app/vector_db

# Exponer puerto
EXPOSE 8080

# Variables de entorno
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production
ENV USE_EMBEDDED_CHROMA=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Comando por defecto
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"] 