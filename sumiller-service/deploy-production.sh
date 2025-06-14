#!/bin/bash
# ===================================
# SCRIPT DE DESPLIEGUE A PRODUCCIÓN
# Sumiller Service - Google Cloud Run
# ===================================

set -e  # Salir si hay errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 DESPLEGANDO SUMILLER SERVICE A PRODUCCIÓN${NC}"
echo "=================================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ] || [ ! -f "Dockerfile" ]; then
    echo -e "${RED}❌ Error: Ejecuta este script desde el directorio sumiller-service${NC}"
    exit 1
fi

# Configuración
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project)}
REGION=${REGION:-europe-west1}
SERVICE_NAME="sumiller-service"

echo -e "${BLUE}📋 Configuración:${NC}"
echo "  Proyecto: $PROJECT_ID"
echo "  Región: $REGION"
echo "  Servicio: $SERVICE_NAME"
echo ""

# Verificar que tenemos la API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY no encontrada en el entorno${NC}"
    echo -e "${YELLOW}   Usando Google Secret Manager...${NC}"
    USE_SECRET_MANAGER=true
else
    echo -e "${GREEN}✅ OPENAI_API_KEY encontrada${NC}"
    USE_SECRET_MANAGER=false
fi

# Función para crear secreto si no existe
create_secret_if_needed() {
    if [ "$USE_SECRET_MANAGER" = true ]; then
        echo -e "${BLUE}🔐 Verificando secreto en Secret Manager...${NC}"
        
        if gcloud secrets describe openai-api-key >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Secreto 'openai-api-key' ya existe${NC}"
        else
            echo -e "${YELLOW}⚠️  Secreto no existe. Creándolo...${NC}"
            echo -e "${RED}❗ IMPORTANTE: Necesitas proporcionar tu API key de OpenAI${NC}"
            echo -n "Introduce tu OPENAI_API_KEY: "
            read -s api_key
            echo ""
            
            if [ -z "$api_key" ]; then
                echo -e "${RED}❌ API key no puede estar vacía${NC}"
                exit 1
            fi
            
            echo "$api_key" | gcloud secrets create openai-api-key --data-file=-
            echo -e "${GREEN}✅ Secreto creado exitosamente${NC}"
        fi
        
        # Dar permisos a Cloud Run
        echo -e "${BLUE}🔑 Configurando permisos...${NC}"
        PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
        gcloud secrets add-iam-policy-binding openai-api-key \
            --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
            --role="roles/secretmanager.secretAccessor" >/dev/null 2>&1 || true
    fi
}

# Función de despliegue
deploy_service() {
    echo -e "${BLUE}🏗️  Construyendo y desplegando...${NC}"
    
    if [ "$USE_SECRET_MANAGER" = true ]; then
        # Despliegue con Secret Manager
        gcloud run deploy $SERVICE_NAME \
            --source . \
            --region $REGION \
            --allow-unauthenticated \
            --memory=1Gi \
            --cpu=1 \
            --max-instances=10 \
            --set-env-vars=ENVIRONMENT=production,LOG_LEVEL=INFO \
            --set-secrets=OPENAI_API_KEY=openai-api-key:latest \
            --quiet
    else
        # Despliegue con variable de entorno directa
        gcloud run deploy $SERVICE_NAME \
            --source . \
            --region $REGION \
            --allow-unauthenticated \
            --memory=1Gi \
            --cpu=1 \
            --max-instances=10 \
            --set-env-vars=ENVIRONMENT=production,LOG_LEVEL=INFO,OPENAI_API_KEY=$OPENAI_API_KEY \
            --quiet
    fi
}

# Función de verificación
verify_deployment() {
    echo -e "${BLUE}🧪 Verificando despliegue...${NC}"
    
    # Obtener URL del servicio
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
    
    if [ -z "$SERVICE_URL" ]; then
        echo -e "${RED}❌ No se pudo obtener la URL del servicio${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}🌐 URL del servicio: $SERVICE_URL${NC}"
    
    # Probar health check
    echo -e "${BLUE}🏥 Probando health check...${NC}"
    sleep 10  # Esperar a que el servicio esté listo
    
    if curl -s -f "$SERVICE_URL/health" >/dev/null; then
        echo -e "${GREEN}✅ Health check exitoso${NC}"
        echo -e "${GREEN}🎉 ¡Despliegue completado exitosamente!${NC}"
        echo ""
        echo -e "${BLUE}📋 Información del servicio:${NC}"
        echo "  URL: $SERVICE_URL"
        echo "  Health: $SERVICE_URL/health"
        echo "  Stats: $SERVICE_URL/stats"
        echo ""
        echo -e "${BLUE}🧪 Comandos de prueba:${NC}"
        echo "  curl $SERVICE_URL/health"
        echo "  curl -X POST $SERVICE_URL/query -H 'Content-Type: application/json' -d '{\"query\": \"vino para paella\", \"user_id\": \"test\"}'"
    else
        echo -e "${RED}❌ Health check falló${NC}"
        echo -e "${YELLOW}⚠️  Revisa los logs: gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --limit=20${NC}"
        exit 1
    fi
}

# Ejecutar despliegue
echo -e "${BLUE}🚀 Iniciando despliegue...${NC}"
create_secret_if_needed
deploy_service
verify_deployment

echo -e "${GREEN}✅ ¡DESPLIEGUE COMPLETADO!${NC}" 