# Scripts - Utilidades de Administración

Esta carpeta contiene scripts de utilidad para administrar el servicio RAG.

## 📁 Scripts Disponibles

### **load_data.py**
Script para cargar datos manualmente desde línea de comandos.

### **backup_knowledge.py**
Crea respaldos de la base de conocimientos y vectores.

### **health_check.py**
Verifica el estado del servicio y sus componentes.

### **reset_database.py**
Reinicia la base de datos vectorial (¡CUIDADO!).

## 🚀 Uso de Scripts

### Carga Manual de Datos
```bash
# Cargar archivo específico
python scripts/load_data.py --file knowledge_base/vinos.json

# Cargar directorio completo
python scripts/load_data.py --directory knowledge_base/

# Forzar recarga
python scripts/load_data.py --directory knowledge_base/ --force
```

### Verificación de Salud
```bash
# Check básico
python scripts/health_check.py

# Check completo con detalles
python scripts/health_check.py --verbose

# Check continuo cada 30 segundos
python scripts/health_check.py --monitor 30
```

### Respaldo de Datos
```bash
# Respaldo completo
python scripts/backup_knowledge.py

# Respaldo con compresión
python scripts/backup_knowledge.py --compress

# Respaldo a ubicación específica
python scripts/backup_knowledge.py --output /path/to/backup/
```

### Reinicio de Base de Datos
```bash
# Reiniciar con confirmación
python scripts/reset_database.py

# Reiniciar sin confirmación (PELIGROSO)
python scripts/reset_database.py --force
```

## ⚙️ Variables de Entorno

Los scripts respetan las mismas variables que el servicio principal:

```bash
export OPENAI_API_KEY="your_key"
export CHROMA_PERSIST_DIRECTORY="/app/chroma_db"
export KNOWLEDGE_BASE_DIR="/app/knowledge_base"
```

## 📊 Logs

Todos los scripts generan logs en:
- Consola (nivel INFO)
- Archivo `logs/scripts.log` (nivel DEBUG)

## 🔧 Desarrollo

Para crear nuevos scripts:

1. Usar el template base
2. Importar utilidades comunes
3. Manejar argumentos con `argparse`
4. Configurar logging apropiado
5. Documentar en este README 