#!/bin/bash

# Script para configurar OpenAI API Key en Google Secret Manager

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Configurando OpenAI API Key en Google Secret Manager${NC}"
echo "========================================================"

# Verificar que gcloud está configurado
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Error: No hay proyecto configurado en gcloud${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Proyecto: $PROJECT_ID${NC}"

# Habilitar API de Secret Manager
echo -e "${YELLOW}🔧 Habilitando API Secret Manager...${NC}"
gcloud services enable secretmanager.googleapis.com

# Solicitar API Key
echo -e "${YELLOW}🔑 Por favor, introduce tu OpenAI API Key:${NC}"
echo -e "${YELLOW}   (Formato: sk-...)"
echo -e "${YELLOW}   La key no se mostrará mientras escribes${NC}"
read -s openai_key

if [ -z "$openai_key" ]; then
    echo -e "${RED}❌ Error: API key no puede estar vacía${NC}"
    exit 1
fi

# Validar formato básico
if [[ ! $openai_key =~ ^sk- ]]; then
    echo -e "${RED}❌ Error: La API key debe comenzar con 'sk-'${NC}"
    exit 1
fi

# Crear o actualizar el secreto
echo -e "${YELLOW}💾 Creando/actualizando secreto...${NC}"
echo -n "$openai_key" | gcloud secrets create openai-api-key --data-file=- 2>/dev/null || \
echo -n "$openai_key" | gcloud secrets versions add openai-api-key --data-file=-

# Verificar que se creó correctamente
if gcloud secrets describe openai-api-key >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Secreto creado/actualizado exitosamente${NC}"
else
    echo -e "${RED}❌ Error: No se pudo crear el secreto${NC}"
    exit 1
fi

# Configurar permisos para Cloud Run
echo -e "${YELLOW}🔑 Configurando permisos para Cloud Run...${NC}"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding openai-api-key \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" >/dev/null 2>&1 || true

echo -e "${GREEN}✅ Permisos configurados${NC}"

# Mostrar información del secreto
echo -e "${BLUE}📋 Información del secreto:${NC}"
gcloud secrets describe openai-api-key --format="table(name,createTime,replication.automatic)"

echo -e "${GREEN}🎉 ¡Configuración completada!${NC}"
echo -e "${BLUE}🚀 Ahora puedes redesplegar el sumiller service${NC}"
echo -e "${BLUE}   Comando: cd sumiller-service && ./deploy-production.sh${NC}" 