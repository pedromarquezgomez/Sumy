# 🧪 **TESTING - Sumiller Service**

## **Resumen**
Suite completa de tests para el **Sumiller Service Autónomo**, incluyendo tests unitarios, de integración y de producción.

---

## **📋 Tipos de Tests**

### **1. Tests Unitarios** (`test_memory.py`)
- ✅ **Módulo de memoria SQLite**
- ✅ **Inicialización de base de datos**
- ✅ **Gestión de conversaciones**
- ✅ **Sistema de preferencias**
- ✅ **Valoraciones de vinos**
- ✅ **Validaciones y errores**

### **2. Tests de Integración** (`test_api.py`)
- ✅ **API FastAPI completa**
- ✅ **Endpoints REST**
- ✅ **Memoria conversacional**
- ✅ **Múltiples usuarios**
- ✅ **Manejo de errores**

### **3. Tests de Producción** (`test_production.py`)
- ✅ **Smoke tests**
- ✅ **Health checks**
- ✅ **Tiempos de respuesta**
- ✅ **Requests concurrentes**
- ✅ **Configuración de producción**

---

## **🚀 Ejecución Rápida**

### **Todos los tests**
```bash
./run-tests.sh
```

### **Tests específicos**
```bash
./run-tests.sh unit          # Solo unitarios
./run-tests.sh integration   # Solo integración
./run-tests.sh production    # Solo producción
./run-tests.sh coverage      # Con cobertura
```

---

## **📦 Instalación de Dependencias**

### **Automática**
```bash
./run-tests.sh install
```

### **Manual**
```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

---

## **🔧 Configuración**

### **Variables de Entorno**

#### **Para Tests Locales**
```bash
# Opcional - se usa clave de prueba si no está configurada
export OPENAI_API_KEY="tu-api-key"
```

#### **Para Tests de Producción**
```bash
# URL del servicio desplegado
export SUMILLER_SERVICE_URL="https://tu-servicio.run.app"
export OPENAI_API_KEY="tu-api-key-real"
```

### **Archivo pytest.ini**
```ini
[tool:pytest]
testpaths = tests
markers =
    unit: Tests unitarios
    integration: Tests de integración
    production: Tests de producción
asyncio_mode = auto
```

---

## **📊 Cobertura de Código**

### **Generar Reporte**
```bash
./run-tests.sh coverage
```

### **Ver Reporte HTML**
```bash
open htmlcov/index.html
```

### **Cobertura Esperada**
- **Memoria SQLite**: >90%
- **API Endpoints**: >85%
- **Funciones Core**: >95%

---

## **🧪 Ejecutar Tests Manualmente**

### **Tests Unitarios**
```bash
pytest tests/test_memory.py -v
```

### **Tests de Integración**
```bash
pytest tests/test_api.py -v
```

### **Tests de Producción**
```bash
# Local (requiere servicio corriendo)
pytest tests/test_production.py -v

# Producción
SUMILLER_SERVICE_URL="https://tu-servicio.run.app" \
pytest tests/test_production.py -v -s
```

### **Tests Específicos**
```bash
# Un test específico
pytest tests/test_memory.py::TestSumillerMemory::test_save_conversation -v

# Tests con marcador
pytest -m "unit" -v

# Tests asíncronos
pytest -m "asyncio" -v
```

---

## **🐛 Debugging Tests**

### **Modo Verbose**
```bash
pytest tests/ -v -s
```

### **Parar en Primer Error**
```bash
pytest tests/ -x
```

### **Mostrar Variables Locales**
```bash
pytest tests/ -l
```

### **Ejecutar Tests Lentos**
```bash
pytest tests/ -m "slow" -v
```

---

## **🔍 Estructura de Tests**

```
tests/
├── test_memory.py      # Tests unitarios (memoria SQLite)
├── test_api.py         # Tests integración (API FastAPI)
├── test_production.py  # Tests producción (smoke tests)
└── __init__.py         # Configuración tests
```

### **Fixtures Principales**
- `temp_db`: Base de datos temporal para tests
- `client`: Cliente FastAPI para tests de API
- `base_url`: URL del servicio para tests de producción

---

## **📈 Métricas de Tests**

### **Objetivos de Calidad**
- ✅ **Cobertura**: >85%
- ✅ **Tests Unitarios**: >20 tests
- ✅ **Tests Integración**: >15 tests
- ✅ **Tests Producción**: >10 tests
- ✅ **Tiempo Ejecución**: <2 minutos

### **Verificaciones Automáticas**
- ✅ **Inicialización SQLite**
- ✅ **Endpoints API funcionando**
- ✅ **Memoria conversacional**
- ✅ **Validaciones de entrada**
- ✅ **Manejo de errores**
- ✅ **Concurrencia**

---

## **🚀 CI/CD Integration**

### **GitHub Actions** (ejemplo)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: ./run-tests.sh unit
      - run: ./run-tests.sh integration
```

### **Google Cloud Build**
```yaml
steps:
  - name: 'python:3.11'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        pip install -r requirements.txt
        ./run-tests.sh all
```

---

## **🎯 Tests por Funcionalidad**

### **Memoria SQLite**
- ✅ Inicialización de tablas
- ✅ Guardar conversaciones
- ✅ Recuperar contexto usuario
- ✅ Gestión de preferencias
- ✅ Sistema de valoraciones
- ✅ Estadísticas del sistema

### **API REST**
- ✅ Health check endpoint
- ✅ Query endpoint (consultas IA)
- ✅ Rate wine endpoint
- ✅ Preferences endpoint
- ✅ User context endpoint
- ✅ Stats endpoint

### **Producción**
- ✅ Servicio disponible
- ✅ Tiempos de respuesta
- ✅ Manejo de carga
- ✅ Configuración correcta
- ✅ Persistencia de datos

---

## **🔧 Troubleshooting**

### **Error: "pytest not found"**
```bash
./run-tests.sh install
```

### **Error: "OpenAI API key"**
```bash
export OPENAI_API_KEY="test-key-for-testing"
```

### **Error: "Service not available"**
```bash
# Para tests de producción, asegurar que el servicio esté corriendo
docker run -p 8080:8080 sumiller-service
```

### **Tests Lentos**
```bash
# Ejecutar solo tests rápidos
pytest tests/ -m "not slow"
```

---

## **📝 Agregar Nuevos Tests**

### **Test Unitario**
```python
@pytest.mark.asyncio
async def test_nueva_funcionalidad(self, temp_db):
    """Test: Nueva funcionalidad"""
    # Arrange
    data = {"test": "data"}
    
    # Act
    result = await temp_db.nueva_funcion(data)
    
    # Assert
    assert result is not None
```

### **Test de API**
```python
def test_nuevo_endpoint(self, client):
    """Test: Nuevo endpoint"""
    response = client.post("/nuevo-endpoint", json={"data": "test"})
    assert response.status_code == 200
```

### **Test de Producción**
```python
@pytest.mark.asyncio
async def test_nueva_funcionalidad_prod(self, base_url, timeout):
    """Test: Nueva funcionalidad en producción"""
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(f"{base_url}/nuevo-endpoint")
        assert response.status_code == 200
```

---

## **✅ Checklist Pre-Deploy**

- [ ] Todos los tests unitarios pasan
- [ ] Todos los tests de integración pasan
- [ ] Cobertura de código >85%
- [ ] Tests de producción configurados
- [ ] Variables de entorno documentadas
- [ ] Scripts de testing funcionando
- [ ] Documentación actualizada

---

**🎉 ¡Suite de tests completa y lista para TFM profesional!** 