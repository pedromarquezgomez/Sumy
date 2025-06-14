# 🚀 Guía de Despliegue a Producción - Agentic RAG Service

## 📋 Opciones de Despliegue

### 🥇 **Opción 1: Script Automático (Recomendado)**

```bash
# Ejecutar script de despliegue
./deploy-production.sh
```

El script maneja automáticamente:
- ✅ Verificación de configuración
- ✅ Construcción de imagen Docker
- ✅ Despliegue a Cloud Run
- ✅ Verificación de funcionamiento

### 🔧 **Opción 2: Comandos Manuales**

#### **Con Variables de Entorno**

```bash
gcloud run deploy agentic-rag-service \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --max-instances=10 \
  --set-env-vars=ENVIRONMENT=production,USE_EMBEDDED_CHROMA=true,OPENAI_API_KEY=sk-tu-key
```

#### **Con Google Secret Manager (Más Seguro)**

```bash
# 1. Crear secreto para API key
echo 'sk-tu-api-key-real' | gcloud secrets create openai-api-key --data-file=-

# 2. Dar permisos a Cloud Run
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# 3. Desplegar
gcloud run deploy agentic-rag-service \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --max-instances=10 \
  --set-env-vars=ENVIRONMENT=production,USE_EMBEDDED_CHROMA=true \
  --set-secrets=OPENAI_API_KEY=openai-api-key:latest
```

### 🏗️ **Opción 3: Cloud Build**

```bash
# Usar cloudbuild.yaml
gcloud builds submit --config cloudbuild.yaml .
```

## 🌍 **Variables de Entorno en Producción**

| Variable | Valor Producción | Descripción |
|----------|------------------|-------------|
| `ENVIRONMENT` | `production` | Entorno de ejecución |
| `USE_EMBEDDED_CHROMA` | `true` | Usar ChromaDB embebido |
| `OPENAI_API_KEY` | `sk-...` | API key de OpenAI (opcional) |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | Modelo a usar |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | URL base de OpenAI |
| `PORT` | `8080` | Puerto (Cloud Run lo maneja) |

## 🧪 **Verificación Post-Despliegue**

### **1. Health Check**
```bash
SERVICE_URL=$(gcloud run services describe agentic-rag-service --region=europe-west1 --format="value(status.url)")
curl $SERVICE_URL/health
```

### **2. Prueba de Consulta RAG**
```bash
curl -X POST $SERVICE_URL/query \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Qué es la inteligencia artificial?", "max_results": 3}'
```

### **3. Agregar Documento de Prueba**
```bash
curl -X POST $SERVICE_URL/documents \
  -H "Content-Type: application/json" \
  -d '{"content": "La inteligencia artificial es una rama de la informática que busca crear sistemas capaces de realizar tareas que normalmente requieren inteligencia humana.", "metadata": {"source": "test", "topic": "AI"}}'
```

## 📊 **Monitoreo en Producción**

### **Logs**
```bash
# Ver logs en tiempo real
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=agentic-rag-service"

# Logs de errores
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=agentic-rag-service AND severity>=ERROR" --limit=50
```

### **Métricas**
```bash
# Información del servicio
gcloud run services describe agentic-rag-service --region=europe-west1

# Revisiones activas
gcloud run revisions list --service=agentic-rag-service --region=europe-west1
```

## 🔄 **Actualizaciones**

### **Actualización Simple**
```bash
# Re-ejecutar script
./deploy-production.sh
```

### **Rollback**
```bash
# Listar revisiones
gcloud run revisions list --service=agentic-rag-service --region=europe-west1

# Hacer rollback a revisión anterior
gcloud run services update-traffic agentic-rag-service \
  --to-revisions=REVISION-NAME=100 \
  --region=europe-west1
```

## 🚨 **Troubleshooting**

### **Error: Memoria insuficiente**
```bash
# Aumentar memoria si es necesario
gcloud run services update agentic-rag-service \
  --memory=4Gi \
  --region=europe-west1
```

### **Error: Timeout en inicialización**
```bash
# Verificar logs de inicialización
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=agentic-rag-service AND textPayload:startup" --limit=10

# Aumentar timeout si es necesario
gcloud run services update agentic-rag-service \
  --timeout=600 \
  --region=europe-west1
```

### **Error: ChromaDB no inicializa**
```bash
# Verificar que USE_EMBEDDED_CHROMA está configurado
gcloud run services describe agentic-rag-service --region=europe-west1 --format="value(spec.template.spec.containers[0].env[].value)"

# Forzar recreación del servicio
gcloud run services replace-traffic agentic-rag-service --to-latest --region=europe-west1
```

### **Error: Health check falla**
```bash
# Ver logs detallados
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=agentic-rag-service" --limit=20

# Verificar variables de entorno
gcloud run services describe agentic-rag-service --region=europe-west1 --format="export"
```

## 💰 **Optimización de Costos**

### **Configuración Recomendada**
```bash
--memory=2Gi              # Necesario para ML models + ChromaDB
--cpu=2                   # 2 vCPU para procesamiento ML
--max-instances=10        # Limitar escalado
--concurrency=50          # Requests simultáneos por instancia (menor por ML)
--timeout=300             # 5 minutos timeout
--min-instances=0         # Scale to zero cuando no hay tráfico
```

### **Configuración Mínima (Desarrollo)**
```bash
--memory=1Gi              # Mínimo para funcionar
--cpu=1                   # 1 vCPU básico
--max-instances=3         # Límite bajo
--concurrency=20          # Menos concurrencia
```

## 🔐 **Gestión de Secretos**

### **Google Secret Manager (Recomendado)**

```bash
# Crear secreto para OpenAI
gcloud secrets create openai-api-key --data-file=-
# Pegar tu API key y presionar Ctrl+D

# Listar secretos
gcloud secrets list

# Actualizar secreto
echo 'nueva-api-key' | gcloud secrets versions add openai-api-key --data-file=-
```

## 🧠 **Consideraciones Específicas del RAG**

### **Base de Datos Vectorial**
- **Producción**: Usar `USE_EMBEDDED_CHROMA=true` (incluido en contenedor)
- **Desarrollo**: Puede usar ChromaDB externo si se prefiere

### **Modelos de ML**
- Los modelos de Sentence Transformers se descargan automáticamente
- Primera inicialización puede tardar más tiempo
- Considerar pre-cargar modelos en imagen Docker para producción

### **Memoria y CPU**
- **Mínimo**: 1Gi RAM, 1 CPU
- **Recomendado**: 2Gi RAM, 2 CPU
- **Alto volumen**: 4Gi RAM, 4 CPU

### **Persistencia de Datos**
- ChromaDB embebido persiste datos en memoria del contenedor
- Para persistencia real, considerar usar Cloud Storage o base de datos externa 