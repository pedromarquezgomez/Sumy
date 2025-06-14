# Agentic RAG Service

Un servicio de RAG (Retrieval-Augmented Generation) agéntico con capacidades avanzadas de búsqueda semántica y generación de respuestas inteligentes.

## 🚀 Características

- **RAG Agéntico**: Sistema inteligente de recuperación y generación aumentada
- **Búsqueda Semántica**: Búsqueda vectorial usando ChromaDB y Sentence Transformers
- **Expansión de Consultas**: Mejora automática de consultas usando LLM
- **API REST**: Endpoints FastAPI para integración fácil
- **Soporte MCP**: Compatible con Model Context Protocol
- **Base de Datos Vectorial**: ChromaDB embebido para producción
- **Tests Completos**: Suite de tests unitarios y de integración

## 📋 Requisitos

- Python 3.11+
- Docker (opcional)
- OpenAI API Key (opcional, para funcionalidades avanzadas)

## 🛠️ Instalación

### Instalación Local

```bash
# Clonar el repositorio
git clone <repository-url>
cd agentic_rag-service

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno (opcional)
export OPENAI_API_KEY=your-api-key-here
export ENVIRONMENT=development
```

### Instalación con Docker

```bash
# Construir imagen
docker build -t agentic-rag-service .

# Ejecutar contenedor
docker run -p 8080:8080 agentic-rag-service
```

## 🚀 Uso

### Ejecutar el Servicio

```bash
# Desarrollo local
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# Producción
uvicorn main:app --host 0.0.0.0 --port 8080
```

### API Endpoints

#### Health Check
```bash
GET /health
```

#### Consulta RAG
```bash
POST /query
Content-Type: application/json

{
  "query": "¿Qué es la inteligencia artificial?",
  "context": {},
  "max_results": 5
}
```

#### Agregar Documento
```bash
POST /documents
Content-Type: application/json

{
  "content": "La inteligencia artificial es...",
  "metadata": {"source": "wikipedia", "topic": "AI"},
  "doc_id": "ai_intro"
}
```

### Ejemplos de Uso

```python
import httpx

# Cliente para el servicio
client = httpx.Client(base_url="http://localhost:8080")

# Agregar un documento
response = client.post("/documents", json={
    "content": "La inteligencia artificial es una rama de la informática...",
    "metadata": {"source": "textbook", "chapter": 1}
})

# Hacer una consulta
response = client.post("/query", json={
    "query": "¿Qué es la inteligencia artificial?",
    "max_results": 3
})

print(response.json())
```

## 🧪 Tests

### Ejecutar Tests Localmente

```bash
# Tests básicos
./run-tests.sh local

# Tests en Docker
./run-tests.sh docker

# Tests completos
./run-tests.sh all
```

### Tests Específicos

```bash
# Tests unitarios
pytest tests/test_rag_engine.py -v

# Tests de API
pytest tests/test_api.py -v

# Tests con coverage
pytest --cov=. --cov-report=html
```

## 🐳 Docker

### Desarrollo

```bash
# Construir imagen de desarrollo
docker build -t agentic-rag-service:dev .

# Ejecutar con volúmenes para desarrollo
docker run -p 8080:8080 -v $(pwd):/app agentic-rag-service:dev
```

### Tests

```bash
# Construir imagen de tests
docker build -f Dockerfile.test -t agentic-rag-service:test .

# Ejecutar tests
docker run --rm agentic-rag-service:test
```

## ☁️ Despliegue en Google Cloud Run

### Despliegue Automático

```bash
# Ejecutar script de despliegue
./deploy-production.sh
```

### Despliegue Manual

```bash
# Configurar proyecto
gcloud config set project maitre-ia

# Construir y subir imagen
docker build -t gcr.io/maitre-ia/agentic-rag-service .
docker push gcr.io/maitre-ia/agentic-rag-service

# Desplegar en Cloud Run
gcloud run deploy agentic-rag-service \
  --image gcr.io/maitre-ia/agentic-rag-service \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

## 🔧 Configuración

### Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `OPENAI_API_KEY` | Clave API de OpenAI | - |
| `OPENAI_BASE_URL` | URL base de OpenAI | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | Modelo de OpenAI | `gpt-3.5-turbo` |
| `USE_EMBEDDED_CHROMA` | Usar ChromaDB embebido | `false` |
| `ENVIRONMENT` | Entorno de ejecución | `development` |

### Configuración de ChromaDB

```python
# Embebido (recomendado para producción)
USE_EMBEDDED_CHROMA=true

# Cliente HTTP (para desarrollo)
USE_EMBEDDED_CHROMA=false
CHROMA_HOST=localhost
CHROMA_PORT=8001
```

## 📊 Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Agentic RAG    │    │   ChromaDB      │
│                 │────│     Engine      │────│  Vector Store   │
│  /query         │    │                 │    │                 │
│  /documents     │    │ • Query Expand  │    │ • Embeddings    │
│  /health        │    │ • Semantic      │    │ • Similarity    │
└─────────────────┘    │   Search        │    │   Search        │
                       │ • Answer Gen    │    └─────────────────┘
                       └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │                 │
                       │ • Query Expand  │
                       │ • Answer Gen    │
                       └─────────────────┘
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🆘 Soporte

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentación**: [Wiki](https://github.com/your-repo/wiki)
- **Email**: support@your-domain.com

## 🔄 Changelog

### v1.0.0
- ✅ Implementación inicial del RAG agéntico
- ✅ API REST completa
- ✅ Soporte para ChromaDB embebido
- ✅ Tests unitarios y de integración
- ✅ Despliegue en Google Cloud Run 