#!/bin/bash
# ================================================
# CLOUD TESTS RUNNER - Sumiller Service
# Ejecuta tests en Google Cloud Shell o localmente
# ================================================

set -e  # Salir si hay errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null)}
REGION=${REGION:-europe-west1}
SERVICE_NAME="sumiller-service"

echo -e "${BLUE}🌟 SUMILLER SERVICE - CLOUD TESTS${NC}"
echo "=============================================="

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [COMANDO] [OPCIONES]"
    echo ""
    echo "Comandos disponibles:"
    echo "  unit        - Ejecutar tests unitarios localmente"
    echo "  build       - Ejecutar tests en Cloud Build"
    echo "  production  - Ejecutar tests contra servicio desplegado"
    echo "  smoke       - Tests rápidos de humo"
    echo "  all         - Ejecutar todos los tests"
    echo ""
    echo "Opciones:"
    echo "  --url URL   - URL específica del servicio (para tests de producción)"
    echo "  --help      - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 unit                    # Tests unitarios"
    echo "  $0 production              # Tests contra servicio desplegado"
    echo "  $0 production --url https://mi-servicio.run.app"
    echo "  $0 build                   # Ejecutar en Cloud Build"
}

# Función para tests unitarios
run_unit_tests() {
    echo -e "${BLUE}🧪 Ejecutando tests unitarios...${NC}"
    
    # Verificar que estamos en el directorio correcto
    if [ ! -f "test_runner.py" ]; then
        echo -e "${RED}❌ Error: Ejecuta este script desde el directorio sumiller-service${NC}"
        exit 1
    fi
    
    # Instalar dependencias si es necesario
    echo -e "${YELLOW}📦 Verificando dependencias...${NC}"
    python3 -c "import pytest" 2>/dev/null || {
        echo -e "${YELLOW}Instalando pytest...${NC}"
        pip3 install --user pytest pytest-asyncio
    }
    
    # Ejecutar tests
    export ENVIRONMENT=test
    python3 test_runner.py
}

# Función para tests en Cloud Build
run_build_tests() {
    echo -e "${BLUE}🏗️  Ejecutando tests en Cloud Build...${NC}"
    
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}❌ Error: PROJECT_ID no configurado${NC}"
        echo "Ejecuta: gcloud config set project TU_PROJECT_ID"
        exit 1
    fi
    
    echo -e "${YELLOW}Proyecto: $PROJECT_ID${NC}"
    echo -e "${YELLOW}Archivo: cloudbuild-tests.yaml${NC}"
    
    gcloud builds submit . --config=cloudbuild-tests.yaml --project=$PROJECT_ID
}

# Función para tests de producción
run_production_tests() {
    local service_url="$1"
    
    echo -e "${BLUE}🚀 Ejecutando tests de producción...${NC}"
    
    # Si no se proporciona URL, intentar obtenerla
    if [ -z "$service_url" ]; then
        echo -e "${YELLOW}Obteniendo URL del servicio desplegado...${NC}"
        
        if command -v gcloud >/dev/null 2>&1; then
            service_url=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)" 2>/dev/null)
        fi
        
        if [ -z "$service_url" ]; then
            echo -e "${RED}❌ Error: No se pudo obtener la URL del servicio${NC}"
            echo "Opciones:"
            echo "1. Proporciona la URL: $0 production --url https://tu-servicio.run.app"
            echo "2. Configura gcloud: gcloud auth login && gcloud config set project TU_PROJECT"
            echo "3. Usa la variable de entorno: export SUMILLER_SERVICE_URL=https://tu-servicio.run.app"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}🌐 URL del servicio: $service_url${NC}"
    
    # Verificar que requests está disponible
    python3 -c "import requests" 2>/dev/null || {
        echo -e "${YELLOW}Instalando requests...${NC}"
        pip3 install --user requests
    }
    
    # Ejecutar tests de producción
    python3 test_production_live.py "$service_url"
}

# Función para smoke tests rápidos
run_smoke_tests() {
    local service_url="$1"
    
    echo -e "${BLUE}💨 Ejecutando smoke tests rápidos...${NC}"
    
    if [ -z "$service_url" ]; then
        if command -v gcloud >/dev/null 2>&1; then
            service_url=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)" 2>/dev/null)
        fi
    fi
    
    if [ -z "$service_url" ]; then
        echo -e "${RED}❌ Error: URL del servicio requerida${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}🌐 Probando: $service_url${NC}"
    
    # Test básico con curl
    echo -n "Health check... "
    if curl -f -s "$service_url/health" >/dev/null; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
        exit 1
    fi
    
    echo -n "Stats endpoint... "
    if curl -f -s "$service_url/stats" >/dev/null; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}🎉 Smoke tests pasaron!${NC}"
}

# Función para ejecutar todos los tests
run_all_tests() {
    local service_url="$1"
    
    echo -e "${BLUE}🎯 Ejecutando TODOS los tests...${NC}"
    echo "=============================================="
    
    echo -e "${YELLOW}Fase 1: Tests unitarios${NC}"
    run_unit_tests
    
    echo -e "${YELLOW}Fase 2: Smoke tests${NC}"
    run_smoke_tests "$service_url"
    
    echo -e "${YELLOW}Fase 3: Tests de producción completos${NC}"
    run_production_tests "$service_url"
    
    echo -e "${GREEN}🎉 ¡TODOS LOS TESTS COMPLETADOS!${NC}"
}

# Parsear argumentos
COMMAND=""
SERVICE_URL=""

while [[ $# -gt 0 ]]; do
    case $1 in
        unit|build|production|smoke|all)
            COMMAND="$1"
            shift
            ;;
        --url)
            SERVICE_URL="$2"
            shift 2
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Argumento desconocido: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Ejecutar comando
case $COMMAND in
    unit)
        run_unit_tests
        ;;
    build)
        run_build_tests
        ;;
    production)
        run_production_tests "$SERVICE_URL"
        ;;
    smoke)
        run_smoke_tests "$SERVICE_URL"
        ;;
    all)
        run_all_tests "$SERVICE_URL"
        ;;
    "")
        echo -e "${YELLOW}⚠️  No se especificó comando${NC}"
        show_help
        exit 1
        ;;
    *)
        echo -e "${RED}❌ Comando desconocido: $COMMAND${NC}"
        show_help
        exit 1
        ;;
esac 