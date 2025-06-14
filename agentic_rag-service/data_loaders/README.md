# Data Loaders - Cargadores de Datos

Esta carpeta contiene scripts especializados para cargar diferentes tipos de datos en el sistema RAG.

## 📁 Scripts Disponibles

### **json_loader.py**
Cargador especializado para archivos JSON con estructura de vinos, bodegas y regiones.

### **text_loader.py**
Procesador de documentos de texto plano con extracción de metadatos.

### **bulk_loader.py**
Cargador masivo para procesar múltiples archivos de una vez.

### **api_loader.py**
Cargador que obtiene datos desde APIs externas (bodegas, precios, etc.).

## 🔧 Uso de los Cargadores

### Carga Individual
```python
from data_loaders.json_loader import JSONLoader

loader = JSONLoader()
await loader.load_file("knowledge_base/vinos.json")
```

### Carga Masiva
```python
from data_loaders.bulk_loader import BulkLoader

bulk = BulkLoader()
await bulk.load_directory("knowledge_base/")
```

### Carga desde API
```python
from data_loaders.api_loader import APILoader

api = APILoader()
await api.load_from_url("https://api.vinos.com/catalog")
```

## 🚀 Ejecución Automática

Los cargadores se ejecutan automáticamente al iniciar el servicio si detectan:

1. **Archivos nuevos** en `knowledge_base/`
2. **Cambios en archivos** existentes
3. **Variables de entorno** de carga forzada

## 📊 Monitoreo

Cada cargador genera logs detallados:

```bash
# Ver logs de carga
docker logs agentic-rag-service | grep "LOADER"

# Estadísticas de documentos cargados
curl http://localhost:8080/health
```

## ⚙️ Configuración

Variables de entorno para cargadores:

```bash
# Forzar recarga completa
FORCE_RELOAD=true

# Directorio de datos
KNOWLEDGE_BASE_DIR=/app/knowledge_base

# APIs externas
WINE_API_URL=https://api.example.com
WINE_API_KEY=your_api_key
``` 