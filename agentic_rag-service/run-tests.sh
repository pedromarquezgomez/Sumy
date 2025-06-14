#!/bin/bash

# Script para ejecutar tests del Agentic RAG Service
# Basado en el script del sumiller-service

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Ejecutando tests para Agentic RAG Service${NC}"

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Error: No se encuentra main.py${NC}"
    echo -e "${RED}Asegúrate de ejecutar este script desde el directorio agentic_rag-service${NC}"
    exit 1
fi

# Función para ejecutar tests localmente
run_local_tests() {
    echo -e "${YELLOW}🏠 Ejecutando tests localmente...${NC}"
    
    # Verificar que pytest está instalado
    if ! command -v pytest &> /dev/null; then
        echo -e "${YELLOW}⚠️ pytest no encontrado, instalando dependencias...${NC}"
        pip install -r requirements.txt
    fi
    
    # Configurar variables de entorno para tests
    export ENVIRONMENT=test
    export USE_EMBEDDED_CHROMA=true
    export OPENAI_API_KEY=test-key
    
    # Ejecutar tests unitarios
    echo -e "${YELLOW}🔬 Ejecutando tests unitarios...${NC}"
    pytest tests/test_rag_engine.py -v --tb=short
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Tests unitarios pasaron${NC}"
    else
        echo -e "${RED}❌ Tests unitarios fallaron${NC}"
        return 1
    fi
    
    # Ejecutar tests de API
    echo -e "${YELLOW}🌐 Ejecutando tests de API...${NC}"
    pytest tests/test_api.py -v --tb=short
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Tests de API pasaron${NC}"
    else
        echo -e "${RED}❌ Tests de API fallaron${NC}"
        return 1
    fi
    
    # Ejecutar todos los tests con coverage
    echo -e "${YELLOW}📊 Ejecutando tests con coverage...${NC}"
    pytest --cov=. --cov-report=term-missing --cov-report=html:htmlcov
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Todos los tests pasaron con coverage${NC}"
        echo -e "${BLUE}📋 Reporte de coverage generado en htmlcov/index.html${NC}"
    else
        echo -e "${RED}❌ Algunos tests fallaron${NC}"
        return 1
    fi
}

# Función para ejecutar tests en Docker
run_docker_tests() {
    echo -e "${YELLOW}🐳 Ejecutando tests en Docker...${NC}"
    
    # Construir imagen de test
    echo -e "${YELLOW}🏗️ Construyendo imagen de test...${NC}"
    docker build -f Dockerfile.test -t agentic-rag-service:test .
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error construyendo imagen de test${NC}"
        return 1
    fi
    
    # Ejecutar tests en contenedor
    echo -e "${YELLOW}🧪 Ejecutando tests en contenedor...${NC}"
    docker run --rm agentic-rag-service:test
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Tests en Docker pasaron${NC}"
    else
        echo -e "${RED}❌ Tests en Docker fallaron${NC}"
        return 1
    fi
}

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}Uso: $0 [OPCIÓN]${NC}"
    echo -e "${BLUE}Opciones:${NC}"
    echo -e "${BLUE}  local     Ejecutar tests localmente (por defecto)${NC}"
    echo -e "${BLUE}  docker    Ejecutar tests en Docker${NC}"
    echo -e "${BLUE}  all       Ejecutar tests localmente y en Docker${NC}"
    echo -e "${BLUE}  help      Mostrar esta ayuda${NC}"
}

# Procesar argumentos
case "${1:-local}" in
    "local")
        run_local_tests
        ;;
    "docker")
        run_docker_tests
        ;;
    "all")
        echo -e "${BLUE}🚀 Ejecutando tests completos (local + Docker)${NC}"
        run_local_tests && run_docker_tests
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Opción no válida: $1${NC}"
        show_help
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    echo -e "${GREEN}🎉 Todos los tests completados exitosamente!${NC}"
else
    echo -e "${RED}💥 Algunos tests fallaron${NC}"
    exit 1
fi 