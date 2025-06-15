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

# ✨ NUEVO: URL del servicio RAG para conocimiento profundo
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "https://agentic-rag-service-597742621765.europe-west1.run.app")

# Configuración del servidor
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))

if not OPENAI_API_KEY:
    logger.warning("⚠️ OPENAI_API_KEY no configurada")
    openai_client = None
else:
    openai_client = AsyncOpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        timeout=30.0  # Aumentar timeout a 30 segundos
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

# ✨ NUEVA FUNCIÓN: Consultar RAG service para conocimiento profundo
async def query_rag_service(query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Consultar el servicio RAG para obtener conocimiento profundo sobre vinos y sumillería.
    """
    try:
        if not RAG_SERVICE_URL:
            logger.warning("⚠️ RAG_SERVICE_URL no configurada")
            return {"answer": "", "sources": [], "error": "RAG service not configured"}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "query": query,
                "context": context or {},
                "max_results": 3
            }
            
            logger.info(f"🤖 Consultando RAG service: {query}")
            response = await client.post(
                f"{RAG_SERVICE_URL}/query",
                json=payload
            )
            
            if response.status_code == 200:
                rag_data = response.json()
                logger.info(f"✅ RAG response: {len(rag_data.get('sources', []))} fuentes encontradas")
                return rag_data
            else:
                logger.error(f"❌ RAG service error: {response.status_code} - {response.text}")
                return {"answer": "", "sources": [], "error": f"RAG service returned {response.status_code}"}
                
    except httpx.TimeoutException:
        logger.error("⏰ Timeout consultando RAG service")
        return {"answer": "", "sources": [], "error": "RAG service timeout"}
    except Exception as e:
        logger.error(f"❌ Error consultando RAG service: {e}")
        return {"answer": "", "sources": [], "error": str(e)}

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
        # Respuesta fallback sin IA - MÁS COMPLETA
        if wines:
            # Seleccionar los mejores vinos (hasta 3)
            top_wines = wines[:3]
            response = "🍷 **Recomendaciones de vinos:**\n\n"
            
            for i, wine in enumerate(top_wines, 1):
                name = wine.get("name", "Vino")
                price = wine.get("price", "N/A")
                region = wine.get("region", "")
                wine_type = wine.get("type", "")
                description = wine.get("description", "")
                pairing = wine.get("pairing", "")
                
                response += f"**{i}. {name}**\n"
                if wine_type:
                    response += f"   • Tipo: {wine_type}\n"
                if region:
                    response += f"   • Región: {region}\n"
                if price != "N/A":
                    response += f"   • Precio: {price}€\n"
                if description:
                    response += f"   • Descripción: {description[:150]}{'...' if len(description) > 150 else ''}\n"
                if pairing:
                    response += f"   • Maridaje: {pairing}\n"
                response += "\n"
            
            return response
        else:
            return "No encontré vinos específicos para tu consulta. ¿Podrías darme más detalles sobre qué tipo de vino buscas? Por ejemplo: color, región, ocasión o presupuesto."
    
    try:
        # Contexto del usuario
        context_info = ""
        if user_context.get("recent_conversations"):
            context_info = f"\nContexto del usuario: Ha consultado recientemente sobre {len(user_context['recent_conversations'])} temas."
        
        if user_context.get("preferences"):
            prefs = user_context["preferences"]
            context_info += f"\nPreferencias del usuario: {json.dumps(prefs, ensure_ascii=False)}"
        
        # Prompt según categoría - MÁS DETALLADO
        if category == "WINE_SEARCH":
            system_prompt = """Eres Sumy, un sumiller experto y apasionado. Tu objetivo es proporcionar recomendaciones de vinos detalladas y útiles.

ESTILO DE RESPUESTA:
- Sé profesional pero cercano y entusiasta
- Proporciona información completa y práctica
- Incluye detalles sobre características organolépticas cuando sea relevante
- Explica por qué recomiendas cada vino
- Añade consejos de servicio o maridaje cuando sea apropiado
- Usa emojis ocasionalmente para hacer la respuesta más amigable

ESTRUCTURA RECOMENDADA:
1. Saludo breve y contextualización
2. Recomendaciones específicas (1-3 vinos)
3. Detalles de cada vino (nombre, precio, región, características)
4. Razones de la recomendación
5. Consejos adicionales si es relevante"""
            
            wines_info = json.dumps(wines, indent=2, ensure_ascii=False) if wines else "No se encontraron vinos específicos"
            user_content = f"""Consulta del cliente: "{query}"

Vinos disponibles en nuestra carta:
{wines_info}

{context_info}

Proporciona una recomendación completa y profesional como sumiller experto. Incluye detalles sobre las características de los vinos, por qué los recomiendas para esta consulta específica, y cualquier consejo adicional que pueda ser útil."""

        elif category == "WINE_THEORY":
            system_prompt = """Eres Sumy, un sumiller experto con amplio conocimiento en enología y viticultura. Tu objetivo es educar y compartir conocimiento de manera clara y completa.

ESTILO DE RESPUESTA:
- Proporciona explicaciones claras y completas
- Usa ejemplos prácticos cuando sea posible
- Incluye contexto histórico o técnico relevante
- Conecta la teoría con la práctica
- Sé didáctico pero no condescendiente
- Incluye consejos prácticos para aplicar el conocimiento

ESTRUCTURA RECOMENDADA:
1. Explicación del concepto principal
2. Detalles técnicos relevantes
3. Ejemplos prácticos o casos de uso
4. Consejos para la aplicación práctica
5. Recomendaciones adicionales si es apropiado"""
            
            user_content = f"""Consulta sobre enología/viticultura: "{query}"

{context_info}

Proporciona una explicación completa y educativa como sumiller experto. Incluye tanto aspectos técnicos como prácticos, y conecta la información con experiencias reales de cata o servicio."""
        
        else:
            # Para otras categorías, usar respuesta predefinida pero más completa
            return CATEGORY_RESPONSES.get(category, "Como sumiller profesional, me especializo en el mundo del vino. Puedo ayudarte con recomendaciones de vinos, maridajes, técnicas de cata, información sobre regiones vitivinícolas, y mucho más. ¿En qué aspecto del vino te gustaría que te asesore?")
        
        response = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7,
            max_tokens=800  # Aumentado significativamente para respuestas más completas
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error generando respuesta IA: {e}")
        # Fallback inteligente - MÁS COMPLETO
        if wines:
            top_wines = wines[:3]
            response = "🍷 **Recomendaciones basadas en tu consulta:**\n\n"
            
            for i, wine in enumerate(top_wines, 1):
                name = wine.get("name", "Vino")
                price = wine.get("price", "N/A")
                region = wine.get("region", "")
                wine_type = wine.get("type", "")
                description = wine.get("description", "")
                
                response += f"**{i}. {name}**\n"
                if wine_type:
                    response += f"   • Tipo: {wine_type}\n"
                if region:
                    response += f"   • Región: {region}\n"
                if price != "N/A":
                    response += f"   • Precio: {price}€\n"
                if description:
                    response += f"   • Características: {description[:200]}{'...' if len(description) > 200 else ''}\n"
                
                # Añadir razón específica basada en la consulta
                query_lower = query.lower()
                if any(word in query_lower for word in ["pescado", "mariscos", "sushi"]):
                    response += f"   • ¿Por qué te lo recomiendo?: Ideal para pescados y mariscos por su frescura y acidez equilibrada\n"
                elif any(word in query_lower for word in ["carne", "cordero", "ternera", "asado"]):
                    response += f"   • ¿Por qué te lo recomiendo?: Perfecto para carnes por su estructura tánica y cuerpo\n"
                elif any(word in query_lower for word in ["queso", "tabla"]):
                    response += f"   • ¿Por qué te lo recomiendo?: Excelente con quesos por su equilibrio y complejidad\n"
                else:
                    response += f"   • ¿Por qué te lo recomiendo?: Recomendado por su excelente relación calidad-precio y versatilidad\n"
                
                response += "\n"
            
            response += "💡 **Consejo del sumiller**: Sirve a la temperatura adecuada y considera decantar si es un tinto con cuerpo para potenciar sus aromas."
            return response
        else:
            return "No encontré vinos específicos para tu consulta, pero estaré encantado de ayudarte. ¿Podrías contarme más detalles? Por ejemplo: ¿qué tipo de vino prefieres (tinto, blanco, rosado)?, ¿para qué ocasión?, ¿tienes algún presupuesto en mente?, ¿hay alguna región que te interese especialmente?"

# ✨ FUNCIÓN MEJORADA: Generar respuesta del sumiller usando RAG + IA
async def generate_sumiller_response_with_rag(
    query: str, 
    rag_response: Dict[str, Any], 
    user_context: Dict[str, Any],
    category: str = "WINE_THEORY"
) -> str:
    """Generar respuesta del sumiller combinando RAG con OpenAI."""
    
    if not openai_client:
        # Respuesta fallback usando solo RAG - MÁS COMPLETA
        if rag_response.get("answer"):
            return rag_response["answer"]
        elif rag_response.get("sources"):
            response = "📚 **Basándome en mi conocimiento especializado:**\n\n"
            
            for i, source in enumerate(rag_response["sources"][:3], 1):
                content = source.get("content", "")
                metadata = source.get("metadata", {})
                
                if metadata.get("type") == "vino":
                    response += f"**{i}. {metadata.get('name', 'Vino')}**\n"
                    response += f"   • Región: {metadata.get('region', 'N/A')}\n"
                    response += f"   • Precio: {metadata.get('price', 'N/A')}€\n"
                    response += f"   • Características: {content[:300]}{'...' if len(content) > 300 else ''}\n\n"
                else:
                    response += f"**Información relevante {i}:**\n"
                    response += f"{content[:400]}{'...' if len(content) > 400 else ''}\n\n"
            
            return response
        else:
            return "No encontré información específica para tu consulta en mi base de conocimientos. ¿Podrías reformular la pregunta o ser más específico sobre qué aspecto del vino te interesa?"
    
    try:
        # Extraer información del RAG
        rag_sources = rag_response.get("sources", [])
        rag_content = ""
        
        if rag_sources:
            rag_content = "Información especializada de mi base de conocimientos:\n\n"
            for i, source in enumerate(rag_sources[:3], 1):
                content = source.get("content", "")
                metadata = source.get("metadata", {})
                
                rag_content += f"Fuente {i}:\n"
                rag_content += f"Tipo: {metadata.get('type', 'información')}\n"
                if metadata.get("name"):
                    rag_content += f"Nombre: {metadata.get('name')}\n"
                rag_content += f"Contenido: {content[:500]}{'...' if len(content) > 500 else ''}\n\n"
        
        # Contexto del usuario
        context_info = ""
        if user_context.get("recent_conversations"):
            context_info = f"Contexto del usuario: Ha consultado recientemente sobre {len(user_context['recent_conversations'])} temas relacionados con vinos."
        
        if user_context.get("preferences"):
            prefs = user_context["preferences"]
            context_info += f"\nPreferencias conocidas: {json.dumps(prefs, ensure_ascii=False)}"
        
        # Prompt especializado para combinar RAG + sumiller - MÁS DETALLADO
        system_prompt = """Eres Sumy, un sumiller profesional con acceso a una extensa base de conocimientos especializada en vinos y enología.

Tu objetivo es proporcionar respuestas completas, educativas y prácticas que combinen:
1. La información técnica y específica de tu base de conocimientos
2. Tu experiencia profesional como sumiller
3. Consejos prácticos y aplicables
4. Recomendaciones personalizadas

ESTILO DE RESPUESTA:
- Combina información técnica con experiencia práctica
- Sé detallado pero accesible
- Incluye ejemplos concretos cuando sea posible
- Proporciona consejos prácticos de servicio, cata o maridaje
- Conecta conceptos teóricos con aplicaciones reales
- Usa un tono profesional pero cercano y entusiasta

ESTRUCTURA RECOMENDADA:
1. Introducción contextualizada a la consulta
2. Información principal basada en tu base de conocimientos
3. Análisis y explicación profesional
4. Recomendaciones específicas o consejos prácticos
5. Sugerencias adicionales o próximos pasos"""
        
        user_content = f"""Consulta del cliente: "{query}"

{rag_content}

{context_info}

Proporciona una respuesta completa y profesional como sumiller experto. Combina la información de tu base de conocimientos con tu experiencia práctica, y asegúrate de incluir consejos útiles y aplicables."""

        response = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7,
            max_tokens=1000  # Aumentado significativamente para respuestas más completas
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error generando respuesta RAG+IA: {e}")
        # Fallback usando solo RAG - MÁS COMPLETO
        if rag_response.get("sources"):
            response = "📚 **Basándome en mi conocimiento especializado:**\n\n"
            
            for i, source in enumerate(rag_response["sources"][:3], 1):
                content = source.get("content", "")
                metadata = source.get("metadata", {})
                
                if metadata.get("type") == "vino":
                    response += f"**{i}. {metadata.get('name', 'Vino recomendado')}**\n"
                    if metadata.get("wine_type"):
                        response += f"   • Tipo: {metadata.get('wine_type')}\n"
                    if metadata.get("region"):
                        response += f"   • Región: {metadata.get('region')}\n"
                    if metadata.get("price"):
                        response += f"   • Precio: {metadata.get('price')}€\n"
                    if metadata.get("pairing"):
                        response += f"   • Maridaje: {metadata.get('pairing')}\n"
                    response += f"   • Descripción: {content[:300]}{'...' if len(content) > 300 else ''}\n\n"
                else:
                    response += f"**Información técnica {i}:**\n"
                    response += f"{content[:400]}{'...' if len(content) > 400 else ''}\n\n"
            
            response += "\n💡 **Como sumiller te recomiendo**: Considera estos factores al elegir y servir el vino para obtener la mejor experiencia."
            return response
        else:
            return "Como sumiller profesional, puedo ayudarte con cualquier consulta sobre vinos. Mi especialidad incluye recomendaciones personalizadas, técnicas de cata, maridajes, información sobre regiones vitivinícolas, y consejos de servicio. ¿En qué aspecto específico del mundo del vino te gustaría que te asesore?"

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
        
        # 1. DETECTAR MENSAJE SECRETO (única clasificación que mantenemos)
        query_lower = request.query.lower()
        secret_triggers = [
            "pedro", "pedrito", "pepe", "perico", 
            "vicky", "victoria", "vicki", "vic"
        ]
        if any(trigger in query_lower for trigger in secret_triggers):
            category = "SECRET_MESSAGE"
            response_text = CATEGORY_RESPONSES.get("SECRET_MESSAGE", "🤫 Mensaje secreto detectado...")
            wines_recommended = []
            used_rag = False
            confidence = 1.0
            user_context = await temp_memory.get_user_context(request.user_id)
        else:
            # 2. SIEMPRE USAR RAG - Dejar que el RAG decida qué contestar
            logger.info("🤖 Consultando RAG service para cualquier consulta...")
            
            # Obtener contexto del usuario
            user_context = await temp_memory.get_user_context(request.user_id)
            
            # Consultar RAG service
            rag_response = await query_rag_service(request.query, user_context)
            
            wines_recommended = []
            used_rag = True
            category = "RAG_RESPONSE"
            confidence = 0.8
            
            if rag_response.get("sources") and not rag_response.get("error"):
                # Procesar fuentes de vinos si las hay
                logger.info(f"🍇 Procesando {len(rag_response['sources'])} fuentes RAG...")
                
                for i, src in enumerate(rag_response["sources"]):
                    logger.info(f"🔍 Fuente {i+1}: {src.get('metadata', {})}")
                    
                    if src.get("metadata", {}).get("type") in ["wine", "vino"]:
                        wine_data = src["metadata"].copy()
                        wine_data["relevance_score"] = src.get("relevance_score", 0)
                        
                        # Extraer descripción del contenido
                        content = src.get("content", "")
                        if "Descripción: " in content:
                            description = content.split("Descripción: ")[1].split("\n")[0]
                            wine_data["description"] = description
                        elif content:
                            lines = content.split("\n")
                            description_lines = [line for line in lines if line.strip() and not line.startswith("Vino:")]
                            if description_lines:
                                wine_data["description"] = description_lines[0][:200]
                        
                        wines_recommended.append(wine_data)
                        logger.info(f"✅ Vino añadido: {wine_data.get('name', 'Unknown')}")
                
                logger.info(f"🍷 Total vinos encontrados: {len(wines_recommended)}")
                
                # Generar respuesta inteligente basada en el contenido RAG
                if wines_recommended:
                    # Si hay vinos, generar respuesta de recomendación
                    response_text = await generate_sumiller_response(
                        request.query, wines_recommended, user_context, "WINE_SEARCH"
                    )
                elif rag_response.get("answer"):
                    # Si hay respuesta teórica del RAG, usarla
                    response_text = await generate_sumiller_response_with_rag(
                        request.query, rag_response, user_context, "WINE_THEORY"
                    )
                else:
                    # Respuesta general basada en las fuentes disponibles
                    response_text = await generate_sumiller_response(
                        request.query, [], user_context, "GENERAL"
                    )
            else:
                # Si RAG falla, respuesta general del sumiller
                logger.warning(f"⚠️ RAG falló: {rag_response.get('error', 'Unknown error')}")
                response_text = await generate_sumiller_response(
                    request.query, [], user_context, "GENERAL"
                )
                used_rag = False
        
        # 3. GUARDAR INTERACCIÓN EN MEMORIA
        await temp_memory.save_conversation(
            request.user_id,
            request.query,
            response_text,
            wines_recommended,
            request.session_id
        )
        
        # 4. RESPUESTA FINAL
        return SumillerResponse(
            response=response_text,
            wines_recommended=wines_recommended,
            user_context=user_context,
            confidence=confidence,
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