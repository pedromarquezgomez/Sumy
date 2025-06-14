# Knowledge Base - Base de Conocimientos

Esta carpeta contiene todos los documentos que el sistema RAG utilizará para generar respuestas.

## 📁 Estructura de Archivos

### **Archivos de Vinos (JSON)**
- `vinos.json` - Base de datos principal de vinos
- `bodegas.json` - Información de bodegas y productores
- `regiones.json` - Datos de regiones vitivinícolas

### **Documentos de Teoría (TXT)**
- `conceptos_sumilleria.txt` - Conceptos básicos de sumillería
- `tecnicas_cata.txt` - Técnicas de cata profesional
- `maridajes.txt` - Guías de maridaje
- `temperaturas_servicio.txt` - Temperaturas óptimas de servicio

## 🍷 Formato de Archivo vinos.json

```json
[
  {
    "name": "Nombre del Vino",
    "type": "Tinto|Blanco|Rosado|Espumoso",
    "region": "Región Vitivinícola",
    "grape": "Variedad de Uva",
    "vintage": "2020",
    "price": 25.50,
    "stock": 45,
    "pairing": "Descripción de maridajes",
    "description": "Descripción detallada del vino",
    "rating": 92,
    "alcohol": 14.5,
    "temperature": "16-18°C",
    "winery": "Nombre de la Bodega"
  }
]
```

## 📝 Formato de Documentos de Texto

Los archivos `.txt` deben contener información estructurada:

```
# Título del Concepto

## Definición
Explicación clara del concepto...

## Características
- Característica 1
- Característica 2

## Ejemplos Prácticos
Ejemplos de aplicación...

## Referencias
Fuentes adicionales...
```

## 🔄 Carga Automática

El sistema carga automáticamente todos los archivos de esta carpeta al iniciar:

1. **Archivos JSON**: Se procesan según su tipo
2. **Archivos TXT**: Se cargan como documentos de texto
3. **Metadata**: Se extrae automáticamente para búsquedas

## 📊 Monitoreo

Para verificar qué documentos están cargados:

```bash
# Endpoint de estadísticas
curl http://localhost:8080/health

# Recursos MCP
curl http://localhost:8080/mcp/resources
```

## 🚀 Agregar Nuevos Documentos

### Método 1: Archivos (Recomendado)
1. Agregar archivo a esta carpeta
2. Reiniciar el servicio
3. Verificar carga en logs

### Método 2: API REST
```bash
curl -X POST http://localhost:8080/documents \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Contenido del documento...",
    "metadata": {"type": "teoria", "source": "manual"}
  }'
```

### Método 3: Herramienta MCP
```python
await call_tool("agregar_documento", {
    "contenido": "Nuevo documento...",
    "metadatos": {"tipo": "concepto"}
})
``` 