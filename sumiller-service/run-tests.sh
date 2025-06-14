#!/bin/bash
# Script para ejecutar tests del Sumiller Service

set -e  # Salir si hay errores

echo "🧪 SUMILLER SERVICE - SUITE DE TESTS"
echo "===================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [OPCIÓN]"
    echo ""
    echo "Opciones:"
    echo "  unit        Ejecutar solo tests unitarios"
    echo "  integration Ejecutar solo tests de integración"
    echo "  production  Ejecutar tests de producción (requiere servicio corriendo)"
    echo "  all         Ejecutar todos los tests (por defecto)"
    echo "  coverage    Ejecutar tests con reporte de cobertura"
    echo "  install     Instalar dependencias de testing"
    echo "  help        Mostrar esta ayuda"
    echo ""
    echo "Variables de entorno:"
    echo "  SUMILLER_SERVICE_URL  URL del servicio para tests de producción"
    echo "  OPENAI_API_KEY        API key de OpenAI (requerida para algunos tests)"
}

# Función para instalar dependencias
install_deps() {
    echo -e "${BLUE}📦 Instalando dependencias de testing...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencias instaladas${NC}"
}

# Función para verificar dependencias
check_deps() {
    if ! python -c "import pytest" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  pytest no encontrado. Instalando dependencias...${NC}"
        install_deps
    fi
}

# Función para tests unitarios
run_unit_tests() {
    echo -e "${BLUE}🔬 Ejecutando tests unitarios...${NC}"
    python3 -m pytest tests/test_memory.py -v -m "not slow"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Tests unitarios pasaron${NC}"
    else
        echo -e "${RED}❌ Tests unitarios fallaron${NC}"
        exit 1
    fi
}

# Función para tests de integración
run_integration_tests() {
    echo -e "${BLUE}🔗 Ejecutando tests de integración...${NC}"
    
    # Verificar que las variables de entorno estén configuradas
    if [ -z "$OPENAI_API_KEY" ]; then
        echo -e "${YELLOW}⚠️  OPENAI_API_KEY no configurada. Usando clave de prueba...${NC}"
        export OPENAI_API_KEY="test-key-for-testing"
    fi
    
    python3 -m pytest tests/test_api.py -v
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Tests de integración pasaron${NC}"
    else
        echo -e "${RED}❌ Tests de integración fallaron${NC}"
        exit 1
    fi
}

# Función para tests de producción
run_production_tests() {
    echo -e "${BLUE}🚀 Ejecutando tests de producción...${NC}"
    
    # Verificar URL del servicio
    if [ -z "$SUMILLER_SERVICE_URL" ]; then
        echo -e "${YELLOW}⚠️  SUMILLER_SERVICE_URL no configurada. Usando localhost...${NC}"
        export SUMILLER_SERVICE_URL="http://localhost:8080"
        
        # Verificar si el servicio está corriendo localmente
        if ! curl -s "$SUMILLER_SERVICE_URL/health" > /dev/null 2>&1; then
            echo -e "${RED}❌ Servicio no disponible en $SUMILLER_SERVICE_URL${NC}"
            echo -e "${YELLOW}💡 Inicia el servicio con: docker run -p 8080:8080 sumiller-service${NC}"
            exit 1
        fi
    fi
    
    echo -e "${BLUE}🎯 Testeando servicio en: $SUMILLER_SERVICE_URL${NC}"
    python3 -m pytest tests/test_production.py -v -s
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Tests de producción pasaron${NC}"
    else
        echo -e "${RED}❌ Tests de producción fallaron${NC}"
        exit 1
    fi
}

# Función para tests con cobertura
run_coverage_tests() {
    echo -e "${BLUE}📊 Ejecutando tests con cobertura...${NC}"
    
    # Verificar que pytest-cov esté instalado
    if ! python -c "import pytest_cov" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  pytest-cov no encontrado. Instalando...${NC}"
        pip install pytest-cov
    fi
    
    python3 -m pytest tests/test_memory.py tests/test_api.py \
        --cov=. \
        --cov-report=html \
        --cov-report=term-missing \
        --cov-report=xml \
        -v
    
    echo -e "${GREEN}✅ Reporte de cobertura generado en htmlcov/index.html${NC}"
}

# Función para ejecutar todos los tests
run_all_tests() {
    echo -e "${BLUE}🎯 Ejecutando suite completa de tests...${NC}"
    
    run_unit_tests
    echo ""
    run_integration_tests
    
    # Tests de producción solo si el servicio está disponible
    if curl -s "${SUMILLER_SERVICE_URL:-http://localhost:8080}/health" > /dev/null 2>&1; then
        echo ""
        run_production_tests
    else
        echo -e "${YELLOW}⚠️  Saltando tests de producción (servicio no disponible)${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}🎉 ¡Todos los tests completados exitosamente!${NC}"
}

# Procesar argumentos
case "${1:-all}" in
    "unit")
        check_deps
        run_unit_tests
        ;;
    "integration")
        check_deps
        run_integration_tests
        ;;
    "production")
        check_deps
        run_production_tests
        ;;
    "all")
        check_deps
        run_all_tests
        ;;
    "coverage")
        check_deps
        run_coverage_tests
        ;;
    "install")
        install_deps
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Opción desconocida: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac 