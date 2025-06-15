#!/usr/bin/env python3
"""
Script para añadir vinos del archivo carta_higueron.json directamente a la base de datos vectorial del RAG
"""

import json
import requests
from pathlib import Path
from typing import List, Dict, Any

# Configuración
RAG_SERVICE_URL = "https://agentic-rag-service-597742621765.europe-west1.run.app"
CARTA_HIGUERON_PATH = "agentic_rag-service/knowledge_base/carta_higueron.json"

def load_wines_from_json(file_path: str) -> List[Dict[str, Any]]:
    """Cargar vinos desde el archivo JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            wines = json.load(f)
        print(f"✅ Cargados {len(wines)} vinos desde {file_path}")
        return wines
    except Exception as e:
        print(f"❌ Error cargando archivo {file_path}: {e}")
        return []

def create_wine_content(wine: Dict[str, Any]) -> str:
    """Crear contenido estructurado para un vino"""
    content = f"""Vino: {wine.get('name', 'Sin nombre')}
Tipo: {wine.get('type', 'Sin tipo')}
Región: {wine.get('region', 'Sin región')}
Uva: {wine.get('grape', 'Sin información de uva')}
Bodega: {wine.get('winery', 'Sin bodega')}
Precio: {wine.get('price', 0)}€
Graduación: {wine.get('alcohol', 0)}% vol.
Temperatura de servicio: {wine.get('temperature', 'Sin información')}
Crianza: {wine.get('crianza', 'Sin información de crianza')}
Descripción: {wine.get('description', 'Sin descripción')}
Maridaje: {wine.get('pairing', 'Sin información de maridaje')}
Puntuación: {wine.get('rating', 0)}/100"""
    
    return content

def create_wine_metadata(wine: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Crear metadata para un vino"""
    return {
        "source": "carta_higueron.json",
        "type": "vino",
        "name": wine.get('name', ''),
        "wine_type": wine.get('type', ''),
        "region": wine.get('region', ''),
        "grape": wine.get('grape', ''),
        "winery": wine.get('winery', ''),
        "vintage": wine.get('vintage', ''),
        "price": wine.get('price', 0),
        "alcohol": wine.get('alcohol', 0),
        "rating": wine.get('rating', 0),
        "pairing": wine.get('pairing', ''),
        "temperature": wine.get('temperature', ''),
        "crianza": wine.get('crianza', ''),
        "index": index,
        "loaded_from": "script_carta_higueron"
    }

def add_document_to_rag(content: str, metadata: Dict[str, Any], doc_id: str) -> bool:
    """Añadir documento al RAG via API"""
    try:
        payload = {
            "content": content,
            "metadata": metadata,
            "doc_id": doc_id
        }
        
        response = requests.post(
            f"{RAG_SERVICE_URL}/documents",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error añadiendo documento {doc_id}: {e}")
        return False

def check_rag_service():
    """Verificar que el servicio RAG esté disponible"""
    try:
        response = requests.get(f"{RAG_SERVICE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Servicio RAG disponible")
            return True
        else:
            print(f"❌ Servicio RAG no disponible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando con RAG: {e}")
        return False

def get_current_documents():
    """Obtener documentos actuales en el RAG"""
    try:
        response = requests.get(f"{RAG_SERVICE_URL}/mcp/resources/knowledge://stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print(f"📊 Documentos actuales en RAG: {stats.get('total_documents', 0)}")
            return stats.get('total_documents', 0)
        else:
            print("⚠️ No se pudo obtener estadísticas del RAG")
            return 0
    except Exception as e:
        print(f"⚠️ Error obteniendo estadísticas: {e}")
        return 0

def main():
    """Función principal"""
    print("🍷 Script para añadir vinos de Carta Higuerón al RAG")
    print("📊 Método: Añadir documentos directamente a la base de datos vectorial")
    print("=" * 60)
    
    # Verificar servicio RAG
    print("\n🔍 Verificando servicio RAG...")
    if not check_rag_service():
        print("❌ No se puede conectar con el servicio RAG")
        return
    
    # Obtener estadísticas actuales
    initial_docs = get_current_documents()
    
    # Cargar vinos
    print(f"\n📁 Cargando vinos desde {CARTA_HIGUERON_PATH}...")
    wines = load_wines_from_json(CARTA_HIGUERON_PATH)
    
    if not wines:
        print("❌ No se pudieron cargar los vinos")
        return
    
    success_count = 0
    total_wines = len(wines)
    
    print(f"\n🚀 Procesando {total_wines} vinos...")
    print("-" * 40)
    
    for i, wine in enumerate(wines):
        wine_name = wine.get('name', f'vino_{i}')
        # Crear ID único y limpio
        clean_name = wine_name.replace(' ', '_').replace('/', '_').replace('&', 'y').replace('.', '')
        doc_id = f"higueron_{i:03d}_{clean_name}"
        
        content = create_wine_content(wine)
        metadata = create_wine_metadata(wine, i)
        
        print(f"📝 [{i+1:2d}/{total_wines}] Añadiendo: {wine_name}")
        
        if add_document_to_rag(content, metadata, doc_id):
            success_count += 1
            print(f"   ✅ Añadido exitosamente (ID: {doc_id})")
        else:
            print(f"   ❌ Error añadiendo")
        
        # Pequeña pausa para no saturar el servicio
        import time
        time.sleep(0.1)
    
    # Verificar estadísticas finales
    print("\n" + "=" * 60)
    print("📊 Verificando resultado...")
    final_docs = get_current_documents()
    added_docs = final_docs - initial_docs
    
    print(f"📊 Resumen:")
    print(f"   📄 Documentos iniciales: {initial_docs}")
    print(f"   📄 Documentos finales: {final_docs}")
    print(f"   ➕ Documentos añadidos: {added_docs}")
    print(f"   🍷 Vinos procesados: {total_wines}")
    print(f"   ✅ Vinos añadidos exitosamente: {success_count}")
    print(f"   ❌ Errores: {total_wines - success_count}")
    
    if success_count == total_wines:
        print("\n🎉 ¡Todos los vinos se añadieron exitosamente a la base de datos vectorial!")
        print("🔍 Los vinos ya están disponibles para búsquedas en el RAG")
    elif success_count > 0:
        print(f"\n⚠️  Se añadieron {success_count} de {total_wines} vinos")
        print("🔍 Los vinos añadidos ya están disponibles para búsquedas")
    else:
        print("\n❌ No se pudo añadir ningún vino")
        print("🔧 Verifica la conectividad con el servicio RAG")

if __name__ == "__main__":
    main() 