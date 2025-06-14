#!/usr/bin/env python3
"""
Sumiller Service - Microservicio Autónomo con Filtro Inteligente
Sumiller inteligente con memoria integrada, búsqueda de vinos y filtro LLM.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Cargar variables de entorno desde .env (solo en desarrollo)
load_dotenv()

# Importar memoria integrada y filtro inteligente
from memory import memory, SumillerMemory
from query_filter import filter_and_classify_query, CATEGORY_RESPONSES

# Configuración de logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, log_level.upper()))
logger = logging.getLogger(__name__)

# Configuración OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Configuración del entorno
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# URL del servicio de búsqueda (opcional)
SEARCH_SERVICE_URL = os.getenv("SEARCH_SERVICE_URL", "")

# Configuración del servidor
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))

if not OPENAI_API_KEY:
    logger.warning("⚠️ OPENAI_API_KEY no configurada")
    openai_client = None
else:
    openai_client = AsyncOpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL
    )
    logger.info(f"✅ OpenAI configurado: {OPENAI_BASE_URL} - Modelo: {OPENAI_MODEL}")

# FastAPI App
app = FastAPI(
    title="Sumiller Service",
    description="Microservicio autónomo de sumiller con memoria integrada y filtro inteligente",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de datos
class QueryRequest(BaseModel):
    query: str
    user_id: str = "default_user"
    session_id: Optional[str] = None

class WineRatingRequest(BaseModel):
    wine_name: str
    rating: int  # 1-5
    notes: str = ""
    user_id: str = "default_user"

class PreferencesRequest(BaseModel):
    preferences: Dict[str, Any]
    user_id: str = "default_user"

class SumillerResponse(BaseModel):
    response: str
    wines_recommended: List[Dict[str, Any]] = []
    user_context: Dict[str, Any] = {}
    confidence: float = 0.8
    query_category: str = "unknown"  # NUEVO: categoría de la consulta
    used_rag: bool = False          # NUEVO: si se usó RAG o no

# Base de conocimientos de vinos (embebida)
WINE_KNOWLEDGE = [
    {
        "name": "Ribera del Duero Reserva",
        "type": "Tinto",
        "region": "Ribera del Duero",
        "grape": "Tempranillo",
        "price": 25.50,
        "pairing": "Carnes rojas, cordero, quesos curados",
        "description": "Vino tinto con crianza en barrica, taninos suaves y notas a frutos rojos.",
        "temperature": "16-18°C"
    },
    {
        "name": "Albariño Rías Baixas",
        "type": "Blanco",
        "region": "Rías Baixas",
        "grape": "Albariño",
        "price": 18.90,
        "pairing": "Mariscos, pescados, paella",
        "description": "Vino blanco fresco con acidez equilibrada y notas cítricas.",
        "temperature": "8-10°C"
    },
    {
        "name": "Rioja Gran Reserva",
        "type": "Tinto",
        "region": "Rioja",
        "grape": "Tempranillo, Garnacha",
        "price": 45.00,
        "pairing": "Caza, carnes asadas, quesos añejos",
        "description": "Vino tinto de larga crianza con complejidad aromática excepcional.",
        "temperature": "17-19°C"
    },
    {
        "name": "Cava Brut Nature",
        "type": "Espumoso",
        "region": "Penedès",
        "grape": "Macabeo, Xarel·lo, Parellada",
        "price": 12.75,
        "pairing": "Aperitivos, mariscos, celebraciones",
        "description": "Espumoso elegante sin azúcar añadido, burbujas finas y persistentes.",
        "temperature": "6-8°C"
    }
]

async def search_wines(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """Búsqueda de vinos en la base de conocimientos local."""
    try:
        # Si hay servicio de búsqueda externo, usarlo
        if SEARCH_SERVICE_URL:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{SEARCH_SERVICE_URL}/search",
                    json={"query": query, "max_results": max_results},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json().get("wines", [])
        
        # Búsqueda local simple
        query_lower = query.lower()
        results = []
        
        for wine in WINE_KNOWLEDGE:
            score = 0
            
            # Buscar en nombre
            if query_lower in wine["name"].lower():
                score += 3
            
            # Buscar en tipo
            if query_lower in wine["type"].lower():
                score += 2
            
            # Buscar en maridaje
            if query_lower in wine["pairing"].lower():
                score += 2
            
            # Buscar en región
            if query_lower in wine["region"].lower():
                score += 1
            
            # Buscar en descripción
            if query_lower in wine["description"].lower():
                score += 1
            
            if score > 0:
                wine_result = wine.copy()
                wine_result["relevance_score"] = score / 10.0
                results.append(wine_result)
        
        # Ordenar por relevancia
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:max_results]
        
    except Exception as e:
        logger.error(f"Error en búsqueda de vinos: {e}")
        return []

async def generate_sumiller_response(
    query: str, 
    wines: List[Dict[str, Any]], 
    user_context: Dict[str, Any],
    category: str = "WINE_SEARCH"
) -> str:
    """Generar respuesta del sumiller usando OpenAI."""
    
    if not openai_client:
        # Respuesta fallback sin IA
        if wines:
            wine_names = [wine.get("name", "Vino") for wine in wines[:3]]
            return f"Te recomiendo estos vinos: {', '.join(wine_names)}. Cada uno tiene características únicas que podrían interesarte."
        else:
            return "No encontré vinos específicos para tu consulta, pero puedo ayudarte con recomendaciones generales."
    
    try:
        # Contexto del usuario
        context_info = ""
        if user_context.get("recent_conversations"):
            context_info = f"\nContexto del usuario: Ha consultado recientemente sobre {len(user_context['recent_conversations'])} temas."
        
        if user_context.get("preferences"):
            prefs = user_context["preferences"]
            context_info += f"\nPreferencias: {json.dumps(prefs, ensure_ascii=False)}"
        
        # Prompt según categoría
        if category == "WINE_SEARCH":
            system_prompt = """Eres Sumy, un sumiller profesional experto. Responde de manera amigable y profesional.
            
Basándote en los vinos encontrados y el contexto del usuario, proporciona recomendaciones específicas y útiles.
Incluye detalles sobre maridajes, temperaturas de servicio y por qué recomiendas cada vino."""
            
            wines_info = json.dumps(wines, indent=2, ensure_ascii=False) if wines else "No se encontraron vinos específicos"
            user_content = f"""Consulta: "{query}"

Vinos encontrados:
{wines_info}

{context_info}

Proporciona una recomendación profesional y personalizada."""

        elif category == "WINE_THEORY":
            system_prompt = """Eres Sumy, un sumiller profesional experto en teoría y técnicas de sumillería.
            
Explica conceptos de manera clara y educativa, con ejemplos prácticos cuando sea apropiado."""
            
            user_content = f"""Consulta sobre teoría de vinos: "{query}"

{context_info}

Proporciona una explicación clara y profesional."""
        
        else:
            # Para otras categorías, usar respuesta predefinida
            return CATEGORY_RESPONSES.get(category, "Como sumiller, me especializo en vinos. ¿En qué puedo ayudarte?")
        
        response = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7,
            max_tokens=400
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error generando respuesta IA: {e}")
        # Fallback
        if wines:
            wine_names = [wine.get("name", "Vino") for wine in wines[:3]]
            return f"Te recomiendo estos vinos: {', '.join(wine_names)}."
        else:
            return "Como sumiller, puedo ayudarte con recomendaciones de vinos. ¿Qué tipo de vino buscas?"

# 🆕 ENDPOINT PRINCIPAL CON FILTRO INTELIGENTE
@app.post("/query", response_model=SumillerResponse)
async def sumiller_query_with_filter(request: QueryRequest = Body(...)):
    """
    ✨ ENDPOINT PRINCIPAL CON FILTRO INTELIGENTE
    Clasifica consultas antes de decidir si usar búsqueda o respuesta directa
    """
    try:
        # Inicializar memoria si es necesario (para tests)
        if memory is None:
            temp_memory = SumillerMemory()
        else:
            temp_memory = memory
        
        # 1. CLASIFICAR CONSULTA CON FILTRO INTELIGENTE
        if openai_client:
            classification = await filter_and_classify_query(openai_client, request.query)
        else:
            # Fallback sin IA
            classification = {
                "category": "WINE_SEARCH",
                "confidence": 0.7,
                "reasoning": "Fallback sin IA",
                "should_use_rag": True
            }
        
        logger.info(f"🔍 Clasificación: {classification}")
        
        # 2. OBTENER CONTEXTO DEL USUARIO
        user_context = await temp_memory.get_user_context(request.user_id)
        
        # 3. DECIDIR ESTRATEGIA SEGÚN CLASIFICACIÓN
        category = classification["category"]
        should_search = classification.get("should_use_rag", False)
        
        wines_recommended = []
        used_rag = False
        
        # 4. GENERAR RESPUESTA SEGÚN CATEGORÍA
        if category in ["SECRET_MESSAGE", "GREETING", "OFF_TOPIC"]:
            # Respuesta predefinida
            response_text = CATEGORY_RESPONSES.get(category, "Como sumiller, me especializo en vinos.")
            
        elif category == "WINE_THEORY":
            # Respuesta teórica con IA
            response_text = await generate_sumiller_response(
                request.query, [], user_context, category
            )
            
        elif category == "WINE_SEARCH" and should_search:
            # Búsqueda de vinos + respuesta con IA
            wines_recommended = await search_wines(request.query)
            used_rag = True
            
            response_text = await generate_sumiller_response(
                request.query, wines_recommended, user_context, category
            )
            
        else:
            # Respuesta general del sumiller
            response_text = await generate_sumiller_response(
                request.query, [], user_context, "WINE_THEORY"
            )
        
        # 5. GUARDAR INTERACCIÓN EN MEMORIA
        await temp_memory.save_conversation(
            request.user_id,
            request.query,
            response_text,
            wines_recommended,
            request.session_id
        )
        
        # 6. RESPUESTA FINAL
        return SumillerResponse(
            response=response_text,
            wines_recommended=wines_recommended,
            user_context=user_context,
            confidence=classification["confidence"],
            query_category=category,
            used_rag=used_rag
        )
        
    except Exception as e:
        logger.error(f"Error en consulta: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando consulta: {str(e)}")

@app.post("/rate-wine")
async def rate_wine(request: WineRatingRequest = Body(...)):
    """Valorar un vino."""
    try:
        # Inicializar memoria si es necesario
        temp_memory = memory if memory is not None else SumillerMemory()
        
        await temp_memory.rate_wine(
            request.user_id,
            request.wine_name,
            request.rating,
            request.notes
        )
        
        return {
            "message": f"Vino '{request.wine_name}' valorado con {request.rating}/5 estrellas",
            "user_id": request.user_id
        }
        
    except Exception as e:
        logger.error(f"Error valorando vino: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/preferences")
async def update_preferences(request: PreferencesRequest = Body(...)):
    """Actualizar preferencias del usuario."""
    try:
        temp_memory = memory if memory is not None else SumillerMemory()
        
        await temp_memory.update_preferences(request.user_id, request.preferences)
        
        return {
            "message": f"Preferencias actualizadas para {request.user_id}",
            "preferences": request.preferences
        }
        
    except Exception as e:
        logger.error(f"Error actualizando preferencias: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/{user_id}/context")
async def get_user_context(user_id: str):
    """Obtener contexto del usuario."""
    try:
        temp_memory = memory if memory is not None else SumillerMemory()
        context = await temp_memory.get_user_context(user_id)
        return context
        
    except Exception as e:
        logger.error(f"Error obteniendo contexto: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check del servicio."""
    try:
        # Verificar memoria
        temp_memory = memory if memory is not None else SumillerMemory()
        memory_stats = await temp_memory.get_stats()
        
        # Verificar OpenAI
        ai_status = "ok" if openai_client else "unavailable"
        
        # Estado general
        status = "healthy" if (memory_stats and ai_status == "ok") else "degraded"
        
        return {
            "status": status,
            "service": "sumiller-service",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": "ok" if memory_stats else "error",
                "ai_service": ai_status,
                "wine_search": "ok"
            },
            "memory_stats": memory_stats
        }
        
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return {
            "status": "error",
            "service": "sumiller-service",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/stats")
async def get_stats():
    """Estadísticas del servicio."""
    try:
        temp_memory = memory if memory is not None else SumillerMemory()
        
        # Intentar obtener estadísticas de memoria
        try:
            memory_stats = await temp_memory.get_stats()
        except Exception as memory_error:
            logger.warning(f"Error obteniendo stats de memoria: {memory_error}")
            memory_stats = {
                "error": "Memory stats unavailable",
                "total_conversations": 0,
                "total_users": 0,
                "total_ratings": 0
            }
        
        return {
            "service": "sumiller-service",
            "version": "2.0.0",
            "memory": memory_stats,
            "wine_database": {
                "total_wines": len(WINE_KNOWLEDGE),
                "regions": list(set(wine["region"] for wine in WINE_KNOWLEDGE)),
                "types": list(set(wine["type"] for wine in WINE_KNOWLEDGE))
            },
            "features": {
                "intelligent_filter": True,
                "memory_system": True,
                "wine_search": True,
                "ai_responses": openai_client is not None
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        # En lugar de lanzar excepción, devolver stats básicas
        return {
            "service": "sumiller-service",
            "version": "2.0.0",
            "error": str(e),
            "wine_database": {
                "total_wines": len(WINE_KNOWLEDGE),
                "regions": list(set(wine["region"] for wine in WINE_KNOWLEDGE)),
                "types": list(set(wine["type"] for wine in WINE_KNOWLEDGE))
            },
            "features": {
                "intelligent_filter": True,
                "memory_system": False,  # Error en memoria
                "wine_search": True,
                "ai_responses": openai_client is not None
            }
        }

# 🆕 ENDPOINT PARA PROBAR CLASIFICACIÓN
@app.post("/classify")
async def test_classification(request: QueryRequest = Body(...)):
    """Endpoint para probar la clasificación de consultas."""
    try:
        if not openai_client:
            return {"error": "OpenAI no configurado"}
        
        classification = await filter_and_classify_query(openai_client, request.query)
        
        return {
            "query": request.query,
            "classification": classification,
            "predefined_response": CATEGORY_RESPONSES.get(classification["category"], "Sin respuesta predefinida")
        }
        
    except Exception as e:
        logger.error(f"Error en clasificación: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info(f"🍷 Iniciando Sumiller Service en {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)