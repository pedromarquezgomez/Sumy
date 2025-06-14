#!/bin/bash

# Script de despliegue para Agentic RAG Service en Google Cloud Run
# Optimizado para producción

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
PROJECT_ID="maitre-ia"
SERVICE_NAME="agentic-rag-service"
REGION="europe-west1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${BLUE}🚀 Iniciando despliegue de Agentic RAG Service${NC}"
echo -e "${BLUE}Proyecto: ${PROJECT_ID}${NC}"
echo -e "${BLUE}Servicio: ${SERVICE_NAME}${NC}"
echo -e "${BLUE}Región: ${REGION}${NC}"

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Error: No se encuentra main.py${NC}"
    echo -e "${RED}Asegúrate de ejecutar este script desde el directorio agentic_rag-service${NC}"
    exit 1
fi

# Verificar que gcloud está configurado
echo -e "${YELLOW}🔍 Verificando configuración de gcloud...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Error: No hay una cuenta activa en gcloud${NC}"
    echo -e "${YELLOW}Ejecuta: gcloud auth login${NC}"
    exit 1
fi

# Configurar proyecto
echo -e "${YELLOW}⚙️ Configurando proyecto...${NC}"
gcloud config set project ${PROJECT_ID}

# Habilitar APIs necesarias
echo -e "${YELLOW}🔧 Habilitando APIs necesarias...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Preguntar por OpenAI API Key si se quiere usar
echo -e "${YELLOW}🔑 Configuración de OpenAI (opcional)${NC}"
read -p "¿Deseas configurar una API Key de OpenAI? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Ingresa tu OpenAI API Key: " OPENAI_KEY
    
    # Crear o actualizar secreto
    echo -e "${YELLOW}🔐 Configurando secreto en Secret Manager...${NC}"
    echo -n "${OPENAI_KEY}" | gcloud secrets create openai-api-key --data-file=- 2>/dev/null || \
    echo -n "${OPENAI_KEY}" | gcloud secrets versions add openai-api-key --data-file=-
    
    # Dar permisos a Cloud Run
    PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
    gcloud secrets add-iam-policy-binding openai-api-key \
        --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
    
    USE_SECRETS="--set-secrets=OPENAI_API_KEY=openai-api-key:latest"
else
    USE_SECRETS=""
fi

# Construir imagen Docker
echo -e "${YELLOW}🏗️ Construyendo imagen Docker...${NC}"
docker build -t ${IMAGE_NAME}:latest .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error construyendo la imagen Docker${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Imagen Docker construida exitosamente${NC}"

# Subir imagen a Container Registry
echo -e "${YELLOW}📤 Subiendo imagen a Container Registry...${NC}"
docker push ${IMAGE_NAME}:latest

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error subiendo la imagen${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Imagen subida exitosamente${NC}"

# Desplegar en Cloud Run
echo -e "${YELLOW}🚀 Desplegando en Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 4Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 100 \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars="ENVIRONMENT=production,USE_EMBEDDED_CHROMA=true,PYTHONUNBUFFERED=1" \
    ${USE_SECRETS}

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error desplegando en Cloud Run${NC}"
    exit 1
fi

# Obtener URL del servicio
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo -e "${GREEN}✅ Despliegue completado exitosamente!${NC}"
echo -e "${GREEN}🌐 URL del servicio: ${SERVICE_URL}${NC}"

# Verificar que el servicio está funcionando
echo -e "${YELLOW}🔍 Verificando que el servicio está funcionando...${NC}"
sleep 10

# Test health check
if curl -f "${SERVICE_URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check exitoso${NC}"
    
    # Test básico de query
    echo -e "${YELLOW}🧪 Realizando test de consulta...${NC}"
    TEST_RESPONSE=$(curl -s -X POST "${SERVICE_URL}/query" \
        -H "Content-Type: application/json" \
        -d '{"query": "¿Qué es un tanino?", "max_results": 3}')
    
    if [[ $TEST_RESPONSE == *"answer"* ]]; then
        echo -e "${GREEN}✅ Test de consulta exitoso${NC}"
    else
        echo -e "${YELLOW}⚠️ Test de consulta no devolvió respuesta esperada${NC}"
    fi
    
    echo -e "${GREEN}🎉 Agentic RAG Service desplegado y funcionando correctamente!${NC}"
else
    echo -e "${YELLOW}⚠️ Health check falló, pero el servicio puede estar iniciándose...${NC}"
    echo -e "${YELLOW}Verifica manualmente: ${SERVICE_URL}/health${NC}"
fi

echo -e "${BLUE}📋 Información del despliegue:${NC}"
echo -e "${BLUE}• Proyecto: ${PROJECT_ID}${NC}"
echo -e "${BLUE}• Servicio: ${SERVICE_NAME}${NC}"
echo -e "${BLUE}• Región: ${REGION}${NC}"
echo -e "${BLUE}• URL: ${SERVICE_URL}${NC}"
echo -e "${BLUE}• Health Check: ${SERVICE_URL}/health${NC}"
echo -e "${BLUE}• Query Endpoint: ${SERVICE_URL}/query${NC}"
echo -e "${BLUE}• Documents Endpoint: ${SERVICE_URL}/documents${NC}"

# Mostrar logs en tiempo real
echo -e "${YELLOW}📊 Mostrando logs del servicio (Ctrl+C para salir)...${NC}"
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}" --format="value(text)"