# 🍷 Sumiller Service

Microservicio **totalmente autónomo** de sumiller inteligente con memoria integrada y búsqueda de vinos.

## 🚀 Características

### ✅ **Totalmente Autónomo**
- **Sin dependencias externas** (Redis, ChromaDB, etc.)
- **Memoria SQLite integrada** para persistencia
- **Base de vinos embebida** para búsquedas
- **Listo para desplegar** en cualquier plataforma

### 🧠 **Inteligencia Artificial**
- **OpenAI GPT-4** para conversaciones naturales
- **Personalidad de sumiller** profesional y amigable
- **Memoria conversacional** personalizada por usuario
- **Recomendaciones contextuales**

### 💾 **Memoria Integrada**
- **Historial de conversaciones** por usuario
- **Preferencias personalizadas** 
- **Valoraciones de vinos** (1-5 estrellas)
- **Estadísticas de uso**

## 📁 Estructura

```
sumiller-service/
├── Dockerfile              # Contenedor autónomo
├── requirements.txt         # Dependencias Python
├── main.py                 # API FastAPI principal
├── memory.py               # Módulo de memoria SQLite
├── cloudbuild.yaml         # Despliegue Google Cloud
└── README.md               # Esta documentación
```

## 🔧 Configuración

### Variables de Entorno

```bash
# OpenAI (requerida)
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_BASE_URL=https://api.openai.com/v1  # opcional
OPENAI_MODEL=gpt-4o-mini                   # opcional

# Servicio de búsqueda externo (opcional)
SEARCH_SERVICE_URL=https://search-service.com  # si existe

# Entorno
ENVIRONMENT=production  # o development
```

## 🚀 Despliegue

### **Local con Docker**

```bash
# Construir imagen
docker build -t sumiller-service .

# Ejecutar contenedor
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=sk-your-key \
  sumiller-service
```

### **Google Cloud Run**

```bash
# Desplegar con Cloud Build
gcloud builds submit --config cloudbuild.yaml .

# O manualmente
gcloud run deploy sumiller-service \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=sk-your-key
```

### **Otras plataformas**
- **Heroku**: `git push heroku main`
- **Railway**: Conectar repositorio
- **Vercel**: Usar como API serverless
- **AWS Lambda**: Con adaptador ASGI

## 📡 API Endpoints

### **🍷 Consulta Principal**
```bash
POST /query
{
  "query": "¿Qué vino recomiendas para una paella?",
  "user_id": "usuario123",
  "session_id": "sesion456"  # opcional
}
```

**Respuesta:**
```json
{
  "response": "Te recomiendo Albariño Rías Baixas...",
  "wines_recommended": [
    {
      "name": "Albariño Rías Baixas",
      "type": "Blanco",
      "region": "Rías Baixas",
      "price": 18.90,
      "temperature": "8-10°C",
      "relevance_score": 0.9
    }
  ],
  "user_context": {
    "total_conversations": 5,
    "favorite_wines": [...]
  },
  "confidence": 0.9
}
```

### **⭐ Valorar Vino**
```bash
POST /rate-wine
{
  "wine_name": "Albariño Rías Baixas",
  "rating": 5,
  "notes": "Perfecto con mariscos",
  "user_id": "usuario123"
}
```

### **⚙️ Preferencias**
```bash
POST /preferences
{
  "preferences": {
    "wine_types": ["blanco", "espumoso"],
    "max_price": 30,
    "regions": ["Rías Baixas", "Penedès"]
  },
  "user_id": "usuario123"
}
```

### **👤 Contexto de Usuario**
```bash
GET /user/{user_id}/context
```

### **🏥 Health Check**
```bash
GET /health
```

### **📊 Estadísticas**
```bash
GET /stats
```

## 🧪 Testing

### **Pruebas con curl**

```bash
# Health check
curl http://localhost:8080/health

# Consulta básica
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "vino tinto para carne", "user_id": "test"}'

# Valorar vino
curl -X POST http://localhost:8080/rate-wine \
  -H "Content-Type: application/json" \
  -d '{"wine_name": "Rioja", "rating": 5, "user_id": "test"}'

# Ver estadísticas
curl http://localhost:8080/stats
```

### **Desarrollo Local**

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python main.py

# O con uvicorn
uvicorn main:app --reload --port 8080
```

## 🍷 Base de Vinos

El servicio incluye una **base de vinos embebida** con:

- **Ribera del Duero Reserva** (Tinto) - €25.50
- **Albariño Rías Baixas** (Blanco) - €18.90  
- **Rioja Gran Reserva** (Tinto) - €45.00
- **Cava Brut Nature** (Espumoso) - €12.75

### **Expandir la base de vinos**

Edita `WINE_KNOWLEDGE` en `main.py`:

```python
WINE_KNOWLEDGE.append({
    "name": "Nuevo Vino",
    "type": "Tinto",
    "region": "Ribera del Duero",
    "grape": "Tempranillo",
    "price": 30.00,
    "pairing": "Carnes rojas",
    "description": "Descripción del vino",
    "temperature": "16-18°C"
})
```

## 💾 Memoria SQLite

### **Tablas creadas automáticamente:**

- `conversations` - Historial de conversaciones
- `user_preferences` - Preferencias por usuario  
- `wine_ratings` - Valoraciones de vinos

### **Ubicación de la base de datos:**
- **Local**: `./memory/sumiller.db`
- **Docker**: `/app/memory/sumiller.db`
- **Cloud**: Volumen persistente (si se configura)

## 🔧 Personalización

### **Cambiar personalidad del sumiller**

Edita `system_prompt` en `generate_sumiller_response()`:

```python
system_prompt = """Eres Sumy, un sumiller [TU PERSONALIDAD AQUÍ]"""
```

### **Integrar servicio de búsqueda externo**

Configura `SEARCH_SERVICE_URL` para usar un servicio RAG externo.

### **Cambiar modelo de IA**

```bash
export OPENAI_MODEL=gpt-4  # o gpt-3.5-turbo
```

## 📊 Monitoreo

### **Logs importantes:**
```bash
# Ver logs en Docker
docker logs sumiller-service

# Ver logs en Cloud Run
gcloud logging read "resource.type=cloud_run_revision"
```

### **Métricas clave:**
- Total de conversaciones
- Usuarios únicos
- Vinos más consultados
- Valoraciones promedio

## 🚨 Troubleshooting

### **Error: OpenAI API key not configured**
```bash
export OPENAI_API_KEY=sk-your-key-here
```

### **Error: SQLite database locked**
- Reiniciar el servicio
- Verificar permisos del directorio `/app/memory`

### **Error: Memory full**
- Limpiar conversaciones antiguas
- Aumentar memoria del contenedor

## 🔄 Actualizaciones

### **Versión 1.0.0**
- ✅ Microservicio autónomo
- ✅ Memoria SQLite integrada
- ✅ Base de vinos embebida
- ✅ API REST completa
- ✅ Despliegue Cloud Run

### **Próximas versiones**
- 🔄 Más vinos en la base de datos
- 🔄 Búsqueda semántica avanzada
- 🔄 Integración con APIs de vinos
- 🔄 Dashboard de administración

---

## 🍷 ¡Listo para usar!

Este microservicio es **completamente autónomo** y puede desplegarse en cualquier plataforma que soporte contenedores Docker.

**¿Necesitas ayuda?** Revisa los logs o contacta al equipo de desarrollo. 