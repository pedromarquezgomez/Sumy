# 🚀 Guía de Despliegue a Producción

## 📋 Opciones de Despliegue

### 🥇 **Opción 1: Script Automático (Recomendado)**

```bash
# Ejecutar script de despliegue
./deploy-production.sh
```

El script maneja automáticamente:
- ✅ Verificación de configuración
- ✅ Gestión de secretos (Google Secret Manager)
- ✅ Despliegue a Cloud Run
- ✅ Verificación de funcionamiento

### 🔧 **Opción 2: Comandos Manuales**

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
gcloud run deploy sumiller-service \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --max-instances=10 \
  --set-env-vars=ENVIRONMENT=production,LOG_LEVEL=INFO \
  --set-secrets=OPENAI_API_KEY=openai-api-key:latest
```

#### **Con Variables de Entorno Directas**

```bash
gcloud run deploy sumiller-service \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --max-instances=10 \
  --set-env-vars=ENVIRONMENT=production,LOG_LEVEL=INFO,OPENAI_API_KEY=sk-tu-key
```

### 🏗️ **Opción 3: Cloud Build**

```bash
# Usar cloudbuild.yaml (requiere secreto creado previamente)
gcloud builds submit --config cloudbuild.yaml .
```

## 🔐 **Gestión de Secretos**

### **Google Secret Manager (Recomendado)**

```bash
# Crear secreto
gcloud secrets create openai-api-key --data-file=-
# Pegar tu API key y presionar Ctrl+D

# Listar secretos
gcloud secrets list

# Ver versiones
gcloud secrets versions list openai-api-key

# Actualizar secreto
echo 'nueva-api-key' | gcloud secrets versions add openai-api-key --data-file=-
```

### **Variables de Entorno**

```bash
# Para desarrollo/testing rápido
export OPENAI_API_KEY=sk-tu-key
gcloud run deploy --set-env-vars=OPENAI_API_KEY=$OPENAI_API_KEY
```

## 🌍 **Variables de Entorno en Producción**

| Variable | Valor Producción | Descripción |
|----------|------------------|-------------|
| `ENVIRONMENT` | `production` | Entorno de ejecución |
| `LOG_LEVEL` | `INFO` o `WARNING` | Nivel de logs |
| `OPENAI_API_KEY` | `sk-...` | API key de OpenAI |
| `OPENAI_MODEL` | `gpt-4o-mini` | Modelo a usar |
| `PORT` | `8080` | Puerto (Cloud Run lo maneja) |

## 🧪 **Verificación Post-Despliegue**

### **1. Health Check**
```bash
SERVICE_URL=$(gcloud run services describe sumiller-service --region=europe-west1 --format="value(status.url)")
curl $SERVICE_URL/health
```

### **2. Prueba Funcional**
```bash
curl -X POST $SERVICE_URL/query \
  -H "Content-Type: application/json" \
  -d '{"query": "vino para paella", "user_id": "test_prod"}'
```

### **3. Estadísticas**
```bash
curl $SERVICE_URL/stats
```

## 📊 **Monitoreo en Producción**

### **Logs**
```bash
# Ver logs en tiempo real
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=sumiller-service"

# Logs de errores
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=sumiller-service AND severity>=ERROR" --limit=50
```

### **Métricas**
```bash
# Información del servicio
gcloud run services describe sumiller-service --region=europe-west1

# Revisiones activas
gcloud run revisions list --service=sumiller-service --region=europe-west1
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
gcloud run revisions list --service=sumiller-service --region=europe-west1

# Hacer rollback a revisión anterior
gcloud run services update-traffic sumiller-service \
  --to-revisions=REVISION-NAME=100 \
  --region=europe-west1
```

## 🚨 **Troubleshooting**

### **Error: Secreto no encontrado**
```bash
# Verificar que existe
gcloud secrets describe openai-api-key

# Recrear si es necesario
echo 'sk-tu-key' | gcloud secrets create openai-api-key --data-file=-
```

### **Error: Permisos insuficientes**
```bash
# Verificar permisos del service account
gcloud projects get-iam-policy $(gcloud config get-value project)

# Dar permisos necesarios
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="serviceAccount:$(gcloud config get-value account)" \
  --role="roles/run.admin"
```

### **Error: Health check falla**
```bash
# Ver logs detallados
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=sumiller-service" --limit=20

# Verificar variables de entorno
gcloud run services describe sumiller-service --region=europe-west1 --format="export"
```

## 💰 **Optimización de Costos**

### **Configuración Recomendada**
```bash
--memory=1Gi              # Suficiente para SQLite + OpenAI
--cpu=1                   # 1 vCPU es suficiente
--max-instances=10        # Limitar escalado
--concurrency=80          # Requests simultáneos por instancia
--timeout=300             # 5 minutos timeout
```

### **Monitoreo de Costos**
- Usar Google Cloud Console → Cloud Run → Métricas
- Configurar alertas de facturación
- Revisar logs de uso mensualmente

## 🎯 **Checklist de Despliegue**

- [ ] ✅ API key de OpenAI configurada
- [ ] ✅ Proyecto de Google Cloud seleccionado
- [ ] ✅ APIs habilitadas (Cloud Run, Secret Manager)
- [ ] ✅ Permisos configurados
- [ ] ✅ Script de despliegue ejecutado
- [ ] ✅ Health check exitoso
- [ ] ✅ Prueba funcional completada
- [ ] ✅ Logs verificados
- [ ] ✅ URL documentada para el equipo

---

## 🆘 **Soporte**

Si tienes problemas:
1. Revisa los logs: `gcloud logging tail`
2. Verifica la configuración: `gcloud run services describe`
3. Prueba localmente: `docker run --env-file .env`
4. Contacta al equipo de desarrollo 