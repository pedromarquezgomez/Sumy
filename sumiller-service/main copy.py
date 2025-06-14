# sumiller-bot/main.py - VERSIÓN CON FILTRO INTELIGENTE
"""
Sumiller Bot con Filtro Inteligente basado en LLM
"""
import os
import sys
import logging
import json
from openai import AsyncOpenAI
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Importar el nuevo filtro
from query_filter import filter_and_classify_query, CATEGORY_RESPONSES
from http_client import resilient_client, close_http_pool

# Configuración existente (sin cambios)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", str(config.sumiller_port if config.is_local() else 8080)))
RAG_MCP_URL = config.rag_mcp_url
MEMORY_MCP_URL = config.memory_mcp_url

# Cliente OpenAI (sin cambios)
OPENAI_API_KEY = config.get_openai_key()
OPENAI_BASE_URL = config.get_openai_base_url()
OPENAI_MODEL = config.get_openai_model()

if not OPENAI_API_KEY:
    logger.warning("No se pudo obtener la OpenAI API Key.")
    openai_client = None
else:
    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    logger.info(f"✅ Cliente OpenAI configurado: {OPENAI_BASE_URL}")

# Lifecycle management (sin cambios)
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando Sumiller Bot con filtro inteligente...")
    try:
        client = await resilient_client.pool.get_client()
        await client.get(f"{RAG_MCP_URL}/health", timeout=5.0)
        logger.info("✅ RAG MCP Server conectado")
    except Exception as e:
        logger.warning(f"⚠️ RAG MCP Server no disponible: {e}")
    
    yield
    
    logger.info("🔒 Cerrando Sumiller Bot...")
    await close_http_pool()

app = FastAPI(
    title="Sumiller Bot API - Con Filtro Inteligente",
    description="Sumiller con filtro LLM que evita consultas innecesarias al RAG",
    version="4.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos (sin cambios)
class Query(BaseModel):
    prompt: str
    user_id: str = "default_user"

class RecommendationResponse(BaseModel):
    response: str
    expanded_queries: List[str] = []
    wines_found: int = 0
    query_category: str = "unknown"  # NUEVO: categoría de la consulta
    used_rag: bool = False          # NUEVO: si se usó RAG o no

# Funciones existentes (sin cambios)
async def search_wines_with_agentic_rag(user_query: str, user_id: str = "default_user") -> Dict[str, Any]:
    """Función existente - sin cambios"""
    logger.info(f"🔍 Búsqueda RAG resiliente para: '{user_query}'")
    try:
        memory_context = await get_user_memory_resilient(user_id)
        rag_payload = {"query": user_query, "max_results": 3}
        if memory_context:
            rag_payload["context"] = memory_context
        
        search_result = await resilient_client.post_with_retry(
            url=f"{RAG_MCP_URL}/query",
            json_data=rag_payload,
            max_retries=3
        )
        
        wines_found = len(search_result.get('sources', []))
        logger.info(f"✅ RAG resiliente encontró {wines_found} vinos")
        return search_result
    except Exception as e:
        logger.error(f"❌ Error en búsqueda resiliente: {e}")
        return await fallback_search_resilient(user_query)

async def get_user_memory_resilient(user_id: str) -> Dict[str, Any]:
    """Función existente - sin cambios"""
    try:
        memory_data = await resilient_client.get_with_retry(
            url=f"{MEMORY_MCP_URL}/memory/{user_id}",
            max_retries=2
        )
        logger.info(f"💾 Memoria recuperada resiliente para {user_id}")
        return memory_data
    except Exception as e:
        logger.warning(f"⚠️ No se pudo recuperar memoria: {e}")
        return {}

async def fallback_search_resilient(user_query: str) -> Dict[str, Any]:
    """Función existente - sin cambios"""
    try:
        result = await resilient_client.post_with_retry(
            url=f"{RAG_MCP_URL}/query",
            json_data={"query": user_query, "max_results": 1},
            max_retries=1
        )
        return result
    except Exception as e:
        logger.error(f"❌ Fallback resiliente falló: {e}")
        return {"sources": [], "expanded_queries": [], "error": "Servicios no disponibles"}

async def save_user_interaction_resilient(user_id: str, query: str, response: str, wines: List[Dict]) -> None:
    """Función existente - sin cambios"""
    try:
        memory_payload = {
            "user_id": user_id,
            "interaction": {
                "query": query,
                "response": response,
                "wines_recommended": [wine.get('metadata', {}).get('name', '') for wine in wines[:3]],
                "timestamp": "auto"
            }
        }
        await resilient_client.post_with_retry(
            url=f"{MEMORY_MCP_URL}/memory/save",
            json_data=memory_payload,
            max_retries=2
        )
    except Exception as e:
        logger.warning(f"⚠️ No se pudo guardar en memoria: {e}")

async def generate_agentic_response(user_query: str, search_result: Dict[str, Any], user_id: str) -> str:
    """Función existente - sin cambios"""
    if not openai_client:
        return f"La API de OpenAI no está configurada. Resultados: {json.dumps(search_result.get('sources', []))}"

    documents = search_result.get('sources', [])
    expanded_queries = search_result.get('expanded_queries', [])
    
    if not documents:
        system_prompt = """Eres Sumy, un sumiller profesional."""
        user_content = f"Consulta: \"{user_query}\"\nNo encontré vinos específicos. Responde como sumiller profesional."
    else:
        system_prompt = """Eres Sumy, sumiller profesional. Responde basándote SOLO en las fuentes proporcionadas."""
        wine_docs = [doc for doc in documents if doc.get('metadata', {}).get('doc_type') != 'teoria_sumiller']
        theory_docs = [doc for doc in documents if doc.get('metadata', {}).get('doc_type') == 'teoria_sumiller']
        
        user_content = f"""Consulta: "{user_query}"
        
VINOS ENCONTRADOS: {json.dumps(wine_docs, indent=2, ensure_ascii=False) if wine_docs else "Sin vinos"}
TEORÍA RELEVANTE: {json.dumps(theory_docs, indent=2, ensure_ascii=False) if theory_docs else "Sin teoría"}
"""
    
    try:
        response = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.3,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generando respuesta: {e}")
        if documents:
            return f"Encontré {len(documents)} vinos relevantes para tu consulta."
        else:
            return "No encontré vinos específicos. ¿Podrías ser más específico?"

# 🆕 NUEVO ENDPOINT PRINCIPAL CON FILTRO INTELIGENTE
@app.post("/query", response_model=RecommendationResponse)
async def handle_intelligent_query(query: Query = Body(...)):
    """
    ✨ ENDPOINT PRINCIPAL CON FILTRO INTELIGENTE
    Clasifica consultas antes de decidir si usar RAG o respuesta directa
    """
    user_prompt = query.prompt
    user_id = query.user_id
    
    logger.info(f"🧠 Consulta inteligente de {user_id}: \"{user_prompt}\"")
    
    # 🔍 PASO 1: CLASIFICAR CONSULTA CON LLM
    if openai_client:
        classification = await filter_and_classify_query(openai_client, user_prompt)
    else:
    # Fallback si no hay OpenAI: asumir que es búsqueda de vinos (excepto si detecta mensaje secreto)
        if any(word in user_prompt.lower() for word in ['vicky', 'pedro', 'mensaje', 'secreto']):
            classification = {
                "category": "SECRET_MESSAGE",
                "confidence": 0.8,
                "reasoning": "Fallback: detectadas keywords de mensaje secreto",
                "should_use_rag": False
            }
        else:
            classification = {
                "category": "WINE_SEARCH",
                "confidence": 0.5,
                "reasoning": "OpenAI no disponible - asumiendo búsqueda de vinos",
                "should_use_rag": True
            }
    
    logger.info(f"🏷️ Clasificación: {classification['category']} (confianza: {classification['confidence']:.2f})")
    logger.info(f"💭 Razón: {classification['reasoning']}")
    
    # 🎯 PASO 2: DECIDIR ACCIÓN BASADA EN CLASIFICACIÓN
    category = classification["category"]
    should_use_rag = classification["should_use_rag"]
    
    if should_use_rag:
        # 🍷 CONSULTA DE BÚSQUEDA DE VINOS - Usar RAG agéntico
        logger.info("📤 Enviando al RAG agéntico")
        search_result = await search_wines_with_agentic_rag(user_prompt, user_id)
        response = await generate_agentic_response(user_prompt, search_result, user_id)
        wines_found = len(search_result.get('sources', []))
        expanded_queries = search_result.get('expanded_queries', [])
        used_rag = True
        
    else:
        # 💬 RESPUESTA DIRECTA SIN RAG
        if category in CATEGORY_RESPONSES:
            response = CATEGORY_RESPONSES[category]
        else:
            # Fallback para categorías no definidas
            response = CATEGORY_RESPONSES["OFF_TOPIC"]
        
        wines_found = 0
        expanded_queries = []
        used_rag = False
        
        logger.info(f"⚡ Respuesta directa para categoría: {category}")
    
    # 💾 PASO 3: GUARDAR INTERACCIÓN (SIEMPRE)
    await save_user_interaction_resilient(
        user_id, 
        user_prompt, 
        response, 
        search_result.get('sources', []) if used_rag else []
    )
    
    # 📊 PASO 4: RETORNAR RESPUESTA ENRIQUECIDA
    return RecommendationResponse(
        response=response,
        expanded_queries=expanded_queries,
        wines_found=wines_found,
        query_category=category,
        used_rag=used_rag
    )

# 🆕 NUEVO ENDPOINT PARA TESTING DEL FILTRO
@app.post("/classify")
async def test_classification(query: Query = Body(...)):
    """
    Endpoint para probar solo la clasificación sin ejecutar acción
    """
    if not openai_client:
        return {"error": "OpenAI no configurado"}
    
    classification = await filter_and_classify_query(openai_client, query.prompt)
    return {
        "query": query.prompt,
        "classification": classification,
        "would_use_rag": classification["should_use_rag"]
    }

# Endpoints existentes (sin cambios)
@app.get("/health")
async def health_check_resilient():
    """Health check con información del filtro"""
    try:
        services_status = {"rag_mcp": False, "memory_mcp": False}
        
        try:
            await resilient_client.get_simple(f"{RAG_MCP_URL}/health")
            services_status["rag_mcp"] = True
        except:
            pass
        
        try:
            await resilient_client.get_simple(f"{MEMORY_MCP_URL}/health")
            services_status["memory_mcp"] = True
        except:
            pass
        
        circuit_info = resilient_client.get_circuit_info()
        all_healthy = services_status["rag_mcp"] and services_status["memory_mcp"]
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "circuit_breaker": circuit_info,
            "services": {
                **services_status,
                "openai": openai_client is not None,
                "intelligent_filter": openai_client is not None  # NUEVO
            },
            "config": {
                "rag_url": RAG_MCP_URL,
                "memory_url": MEMORY_MCP_URL,
                "openai_model": OPENAI_MODEL,
                "filter_enabled": openai_client is not None  # NUEVO
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/stats")
async def get_stats_resilient():
    """Estadísticas incluyendo info del filtro"""
    try:
        stats = {"rag_stats": {}, "memory_stats": {}, "client_stats": {}}
        
        try:
            rag_stats = await resilient_client.get_with_retry(f"{RAG_MCP_URL}/stats", max_retries=1)
            stats["rag_stats"] = rag_stats
        except Exception as e:
            stats["rag_stats"] = {"error": str(e)}
        
        try:
            memory_stats = await resilient_client.get_with_retry(f"{MEMORY_MCP_URL}/stats", max_retries=1)
            stats["memory_stats"] = memory_stats
        except Exception as e:
            stats["memory_stats"] = {"error": str(e)}
        
        stats["client_stats"] = {
            "circuit_breaker": resilient_client.get_circuit_info(),
            "pool_initialized": resilient_client.pool._client is not None,
            "intelligent_filter_enabled": openai_client is not None  # NUEVO
        }
        
        return stats
    except Exception as e:
        return {"error": f"No se pudieron obtener estadísticas: {e}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)