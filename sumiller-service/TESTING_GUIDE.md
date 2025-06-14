# 🧪 Guía de Testing - Sumiller Service

Esta guía explica cómo ejecutar tests del Sumiller Service en diferentes entornos de Google Cloud.

## 🚀 Opciones de Testing Disponibles

### 1. **Tests Unitarios** 
Ejecuta tests sin dependencias externas usando mocks.

```bash
# Opción 1: Script unificado
./run_cloud_tests.sh unit

# Opción 2: Directamente
python3 test_runner.py

# Opción 3: Pytest específico
python3 -m pytest tests/test_memory.py -v
```

### 2. **Smoke Tests** 
Tests rápidos contra el servicio desplegado.

```bash
# Automático (detecta URL del servicio)
./run_cloud_tests.sh smoke

# Con URL específica
./run_cloud_tests.sh smoke --url https://tu-servicio.run.app
```

### 3. **Tests de Producción**
Tests exhaustivos contra el servicio real.

```bash
# Automático
./run_cloud_tests.sh production

# Con URL específica  
./run_cloud_tests.sh production --url https://tu-servicio.run.app

# Directamente
python3 test_production_live.py https://tu-servicio.run.app
```

### 4. **CI/CD con Cloud Build**
Tests automáticos en la nube.

```bash
# Ejecutar manualmente
./run_cloud_tests.sh build

# O directamente
gcloud builds submit . --config=cloudbuild-tests.yaml
```

### 5. **Suite Completa**
Ejecuta todos los tests en secuencia.

```bash
./run_cloud_tests.sh all
```

## 🏗️ Configuración de CI/CD Automático

### Crear Trigger para GitHub
```bash
gcloud builds triggers create github \
    --repo-name=tu-repositorio \
    --repo-owner=tu-usuario \
    --branch-pattern='^main$' \
    --build-config=cloudbuild-tests.yaml \
    --description='Tests automáticos del Sumiller Service'
```

### Crear Trigger para Cloud Source Repositories
```bash
gcloud builds triggers create cloud-source-repositories \
    --repo=tu-repositorio \
    --branch-pattern='^main$' \
    --build-config=cloudbuild-tests.yaml
```

### Trigger Automático en cada Push
```bash
# Configurar webhook (si usas GitHub)
gcloud builds triggers create github \
    --repo-name=sumiller-service \
    --repo-owner=tu-usuario \
    --push-branch='^main$' \
    --build-config=cloudbuild-tests.yaml
```

## 🌟 Uso en Cloud Shell

### 1. Clonar y Preparar
```bash
# En Cloud Shell
git clone https://github.com/tu-usuario/tu-repositorio.git
cd tu-repositorio/sumiller-service

# Dar permisos
chmod +x run_cloud_tests.sh test_production_live.py
```

### 2. Ejecutar Tests
```bash
# Tests rápidos
./run_cloud_tests.sh smoke

# Tests completos
./run_cloud_tests.sh production
```

## 🔧 Variables de Entorno

### Para Tests Locales
```bash
export ENVIRONMENT=test
export SQLITE_DB_PATH=:memory:
export OPENAI_API_KEY=test-key-not-used
```

### Para Tests de Producción
```bash
export SUMILLER_SERVICE_URL=https://tu-servicio.run.app
```

## 📊 Interpretación de Resultados

### ✅ Tests Exitosos
- **Unit Tests**: Todos los componentes funcionan correctamente
- **Smoke Tests**: Servicio responde y está accesible
- **Production Tests**: Funcionalidad completa verificada

### ❌ Tests Fallidos
- Revisar logs específicos
- Verificar conectividad
- Comprobar variables de entorno
- Revisar estado del servicio

## 🎯 Casos de Uso Comunes

### Desarrollo Local
```bash
# Antes de hacer commit
./run_cloud_tests.sh unit
```

### Antes de Despliegue
```bash
# Verificar que todo funciona
./run_cloud_tests.sh all
```

### Monitoreo de Producción
```bash
# Tests periódicos
./run_cloud_tests.sh smoke
```

### Debug de Issues
```bash
# Tests detallados
./run_cloud_tests.sh production --url https://problema-servicio.run.app
```

## 🔄 Automatización Avanzada

### Cron Job en Cloud Scheduler
```bash
# Crear job para tests periódicos
gcloud scheduler jobs create http tests-periodicos \
    --schedule="0 */6 * * *" \
    --uri="https://cloudbuild.googleapis.com/v1/projects/TU-PROJECT/triggers/TU-TRIGGER-ID:run" \
    --http-method=POST \
    --headers="Authorization=Bearer $(gcloud auth print-access-token)"
```

### Webhook Post-Despliegue
Configura un webhook que ejecute tests después de cada despliegue exitoso.

## 🆘 Troubleshooting

### Error: "URL del servicio requerida"
```bash
# Solución 1: Configurar gcloud
gcloud auth login
gcloud config set project tu-project-id

# Solución 2: Usar URL directa
./run_cloud_tests.sh production --url https://tu-servicio.run.app

# Solución 3: Variable de entorno
export SUMILLER_SERVICE_URL=https://tu-servicio.run.app
```

### Error: "pytest no encontrado"
```bash
# En Cloud Shell o local
pip3 install --user pytest pytest-asyncio requests
```

### Error: "Permission denied"
```bash
chmod +x run_cloud_tests.sh test_production_live.py
```

## 📈 Métricas y Reporting

Los tests generan métricas automáticamente:
- Tiempo de respuesta de endpoints
- Éxito/fallo de funcionalidades
- Estado de la base de datos
- Performance del servicio

## 🎉 ¡Todo Listo!

Tu sistema de testing está completamente configurado para Google Cloud. 
Puedes ejecutar tests localmente, en CI/CD, o contra servicios desplegados. 