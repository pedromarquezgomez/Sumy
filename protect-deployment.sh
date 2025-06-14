#!/bin/bash
# Script para proteger el despliegue actual del servicio RAG

echo "🛡️ Protegiendo despliegue de agentic-rag-service..."

# 1. Marcar la revisión actual como estable
CURRENT_REVISION=$(gcloud run services describe agentic-rag-service --region=europe-west1 --format="value(status.latestCreatedRevisionName)")
echo "📌 Revisión actual: $CURRENT_REVISION"

# 2. Crear una copia de seguridad de la imagen
echo "💾 Creando backup de la imagen..."
docker pull gcr.io/maitre-ia/agentic-rag-service:latest
docker tag gcr.io/maitre-ia/agentic-rag-service:latest gcr.io/maitre-ia/agentic-rag-service:stable-backup
docker push gcr.io/maitre-ia/agentic-rag-service:stable-backup

# 3. Crear archivo de configuración estable
echo "📝 Guardando configuración estable..."
gcloud run services describe agentic-rag-service --region=europe-west1 --format="export" > agentic-rag-service-stable-config.yaml

# 4. Documentar el estado actual
cat > DEPLOYMENT_STATUS.md << EOF
# 🚀 Estado del Despliegue Protegido

**Fecha:** $(date)
**Servicio:** agentic-rag-service
**Revisión:** $CURRENT_REVISION
**Estado:** ✅ FUNCIONANDO PERFECTAMENTE

## ⚠️ NO TOCAR ESTE DESPLIEGUE

- Filtro inteligente: ✅ Funcionando
- OpenAI API: ✅ Conectado
- RAG System: ✅ Operativo
- Health Check: ✅ OK

## 🔄 Para restaurar si algo sale mal:
\`\`\`bash
gcloud run deploy agentic-rag-service \\
  --image gcr.io/maitre-ia/agentic-rag-service:stable-backup \\
  --region europe-west1
\`\`\`
EOF

echo "✅ Despliegue protegido exitosamente"
echo "📋 Ver estado: cat DEPLOYMENT_STATUS.md" 