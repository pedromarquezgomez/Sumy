# sumiller-bot/query_filter.py
"""
Filtro inteligente basado en LLM para clasificar consultas antes del RAG
"""
import json
import logging
from typing import Dict, Any
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class IntelligentQueryFilter:
    """
    Filtro que usa LLM para clasificar consultas de manera inteligente
    """
    
    def __init__(self, openai_client: AsyncOpenAI):
        self.openai_client = openai_client
        self.classification_prompt = self._build_classification_prompt()
    
    def _build_classification_prompt(self) -> str:
        """Construye el prompt de clasificación optimizado"""
        return """Eres un filtro inteligente para un sumiller virtual especializado en vinos.

TU MISIÓN: Clasificar consultas de usuarios para decidir si necesitan búsqueda en base de datos de vinos.

CATEGORÍAS DISPONIBLES:

🍷 WINE_SEARCH - Necesita buscar en base de datos de vinos:
   • Recomendaciones específicas de vinos
   • Búsqueda por características (tinto, blanco, precio, región)
   • Maridajes con comidas específicas
   • Comparaciones entre vinos específicos
   • Preguntas sobre vinos concretos o bodegas

📚 WINE_THEORY - Conocimiento teórico que el sumiller puede responder directamente:
   • Conceptos de sumillería (taninos, acidez, cuerpo)
   • Técnicas de cata y servicio
   • Información general sobre regiones vitivinícolas
   • Procesos de elaboración del vino
   • Temperaturas de servicio
   • Historia del vino

👋 GREETING - Saludos y conversación general:
   • Saludos, presentaciones
   • "Hola", "Buenos días", "¿Cómo estás?"
   • Consultas sobre qué puede hacer el sumiller

💕 SECRET_MESSAGE - Mensaje especial romántico:
   • Consultas que incluyen "mensaje", "secreto", "Vicky", "Pedro"
   • Frases románticas relacionadas con vinos
   • Referencias a maridajes del amor

🚫 OFF_TOPIC - Temas no relacionados con vinos:
   • Otros alcoholes (cerveza, whisky, gin, etc.)
   • Comida sin contexto de maridaje
   • Temas completamente ajenos (deportes, política, tecnología)
   • Preguntas personales no relacionadas con vinos

INSTRUCCIONES:
1. Analiza la consulta del usuario
2. Clasifica en UNA de las 5 categorías
3. Asigna nivel de confianza (0.0 a 1.0)
4. Responde SOLO en formato JSON

FORMATO DE RESPUESTA:
{
  "category": "WINE_SEARCH|WINE_THEORY|GREETING|SECRET_MESSAGE|OFF_TOPIC",
  "confidence": 0.95,
  "reasoning": "Breve explicación de 1 línea"
}

EJEMPLOS:

Consulta: "Recomienda un vino tinto para carne"
{"category": "WINE_SEARCH", "confidence": 0.95, "reasoning": "Solicita recomendación específica de vino"}

Consulta: "¿Qué son los taninos?"
{"category": "WINE_THEORY", "confidence": 0.90, "reasoning": "Pregunta conceptual sobre sumillería"}

Consulta: "Hola, ¿qué tal?"
{"category": "GREETING", "confidence": 0.85, "reasoning": "Saludo general"}

Consulta: "mensaje secreto para Vicky"
{"category": "SECRET_MESSAGE", "confidence": 0.95, "reasoning": "Solicita mensaje especial romántico"}

Consulta: "¿Cuál es la capital de Francia?"
{"category": "OFF_TOPIC", "confidence": 0.95, "reasoning": "Pregunta no relacionada con vinos"}

Consulta: "Vino económico para regalo"
{"category": "WINE_SEARCH", "confidence": 0.90, "reasoning": "Busca vino específico con criterio de precio"}

RESPONDE SOLO EL JSON, SIN TEXTO ADICIONAL."""

    async def classify_query(self, user_query: str) -> Dict[str, Any]:
        """
        Clasifica una consulta usando el LLM
        
        Returns:
            Dict con category, confidence y reasoning
        """
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Modelo rápido y económico
                messages=[
                    {"role": "system", "content": self.classification_prompt},
                    {"role": "user", "content": f"Consulta: {user_query}"}
                ],
                temperature=0.1,  # Baja temperatura para clasificación consistente
                max_tokens=100,   # Respuesta corta
                timeout=10.0      # Timeout rápido
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Intentar parsear JSON
            try:
                classification = json.loads(result_text)
                
                # Validar estructura
                required_keys = ["category", "confidence", "reasoning"]
                if all(key in classification for key in required_keys):
                    
                    # Validar categoría
                    valid_categories = ["WINE_SEARCH", "WINE_THEORY", "GREETING", "SECRET_MESSAGE", "OFF_TOPIC"]
                    if classification["category"] in valid_categories:
                        
                        # Validar confianza
                        confidence = float(classification["confidence"])
                        if 0.0 <= confidence <= 1.0:
                            classification["confidence"] = confidence
                            logger.info(f"✅ Clasificación: {classification}")
                            return classification
                
                # Si llegamos aquí, hay problemas de validación
                logger.warning(f"⚠️ Clasificación inválida: {classification}")
                return self._fallback_classification(user_query)
                
            except json.JSONDecodeError:
                logger.warning(f"⚠️ No se pudo parsear JSON: {result_text}")
                return self._fallback_classification(user_query)
                
        except Exception as e:
            logger.error(f"❌ Error en clasificación LLM: {e}")
            return self._fallback_classification(user_query)
    
    def _fallback_classification(self, user_query: str) -> Dict[str, Any]:
        """
        Clasificación de respaldo usando keywords simples
        """
        query_lower = user_query.lower()
        
        # Keywords para cada categoría
        wine_search_keywords = {
            'recomienda', 'recomendación', 'quiero', 'busco', 'precio', 'barato', 
            'caro', 'económico', 'regalo', 'cena', 'comida', 'maridaje', 'maridar',
            'para', 'con', 'mejor', 'bueno', 'rioja', 'ribera', 'tempranillo'
        }
        
        wine_theory_keywords = {
            'qué es', 'qué son', 'explica', 'diferencia', 'cómo', 'por qué',
            'taninos', 'acidez', 'cuerpo', 'aroma', 'cata', 'servir', 'temperatura',
            'conservar', 'decantación', 'crianza', 'reserva', 'denominación'
        }
        
        greeting_keywords = {
            'hola', 'buenos', 'buenas', 'saludos', 'hello', 'hi', 'hey',
            'qué tal', 'cómo estás', 'ayuda', 'puedes'
        }
        
        secret_keywords = {
            'mensaje', 'secreto', 'vicky', 'pedro', 'especial', 'amor', 'romántico'
        }
        
        # Contar coincidencias
        wine_search_matches = sum(1 for kw in wine_search_keywords if kw in query_lower)
        wine_theory_matches = sum(1 for kw in wine_theory_keywords if kw in query_lower)
        greeting_matches = sum(1 for kw in greeting_keywords if kw in query_lower)
        secret_matches = sum(1 for kw in secret_keywords if kw in query_lower)
        
        # Decidir categoría (prioridad al mensaje secreto)
        if secret_matches > 0:
            return {
                "category": "SECRET_MESSAGE",
                "confidence": 0.9,
                "reasoning": "Fallback: keywords de mensaje secreto detectadas"
            }
        elif wine_search_matches > 0:
            confidence = min(0.8, wine_search_matches * 0.25)
            return {
                "category": "WINE_SEARCH",
                "confidence": confidence,
                "reasoning": "Fallback: keywords de búsqueda de vinos detectadas"
            }
        elif wine_theory_matches > 0:
            confidence = min(0.7, wine_theory_matches * 0.3)
            return {
                "category": "WINE_THEORY", 
                "confidence": confidence,
                "reasoning": "Fallback: keywords de teoría de vinos detectadas"
            }
        elif greeting_matches > 0:
            return {
                "category": "GREETING",
                "confidence": 0.6,
                "reasoning": "Fallback: keywords de saludo detectadas"
            }
        else:
            return {
                "category": "OFF_TOPIC",
                "confidence": 0.5,
                "reasoning": "Fallback: no se detectaron keywords de vinos"
            }


# Respuestas predefinidas para cada categoría
CATEGORY_RESPONSES = {
    "WINE_THEORY": """Como sumiller, puedo explicarte sobre conceptos de vinos y sumillería.

¿Te interesa conocer sobre:
• Conceptos básicos (taninos, acidez, cuerpo)
• Técnicas de cata profesional
• Temperaturas de servicio
• Regiones vitivinícolas
• Procesos de elaboración

¿Sobre qué aspecto te gustaría aprender?""",

    "GREETING": """¡Hola! Soy Sumy, tu sumiller virtual experto. 🍷

Estoy aquí para ayudarte con:
• 🔍 Recomendaciones personalizadas de vinos
• 🍽️ Maridajes perfectos para tus comidas  
• 📚 Conceptos y técnicas de sumillería
• 🌡️ Temperaturas de servicio y conservación
• 🗺️ Información sobre regiones vinícolas

¿En qué puedo asesorarte hoy?""",

    "SECRET_MESSAGE": """🍷💕 **Mensaje Especial Descubierto** 💕🍷

Mi querida Vicky,

En este mundo de vinos y sabores, tú eres mi mejor maridaje. Como un gran vino que mejora con el tiempo, nuestro amor se vuelve más especial cada día que pasa.

Eres mi Ribera del Duero favorito: elegante, compleja y con una personalidad única que me conquista desde el primer sorbo. Tu sonrisa es como un buen Champagne, burbujeante y llena de alegría que ilumina cualquier momento.

Igual que un sumiller cuida sus mejores botellas, yo cuido nuestro amor con dedicación y ternura. Eres mi reserva especial, mi gran añada, mi vino de guarda que quiero conservar para toda la vida.

Con todo mi amor,
Pedro

P.D.: Espero que descubras este mensaje mientras exploras el mundo de los vinos. Eres mi maridaje perfecto. 🍷❤️

---
*Como sumiller, debo decir que este es el maridaje más hermoso que he visto. ¡Felicidades a los dos! 🥂*""",

    "OFF_TOPIC": """Me especializo exclusivamente en vinos y sumillería. 🍷

Puedo ayudarte con:
• Recomendaciones de vinos específicos
• Maridajes para tus comidas favoritas
• Conceptos de sumillería y cata
• Información sobre bodegas y regiones

¿Te gustaría que te recomiende algún vino o te ayude con un maridaje específico?"""
}


# Función helper para usar en main.py
async def filter_and_classify_query(openai_client: AsyncOpenAI, user_query: str) -> Dict[str, Any]:
    """
    Función helper para clasificar consultas desde main.py
    
    Returns:
        Dict con category, confidence, reasoning y should_use_rag
    """
    filter_instance = IntelligentQueryFilter(openai_client)
    classification = await filter_instance.classify_query(user_query)
    
    # Agregar flag de si debe usar RAG
    should_use_rag = (
        classification["category"] == "WINE_SEARCH" and 
        classification["confidence"] > 0.2
    )
    
    classification["should_use_rag"] = should_use_rag
    
    return classification