#!/usr/bin/env python3
"""
Módulo de Memoria Integrada para Sumiller Service
Usa SQLite para persistencia local sin dependencias externas.
"""

import sqlite3
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class SumillerMemory:
    """Gestión de memoria conversacional y preferencias del usuario."""
    
    def __init__(self, db_path: str = None):
        # Usar variable de entorno o valor por defecto
        if db_path is None:
            db_path = os.getenv("SQLITE_DB_PATH", "/app/memory/sumiller.db")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Inicializar base de datos SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    wines_recommended TEXT,  -- JSON
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    preferences TEXT NOT NULL,  -- JSON
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS wine_ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    wine_name TEXT NOT NULL,
                    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                    notes TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("✅ Base de datos de memoria inicializada")
    
    async def save_conversation(
        self, 
        user_id: str, 
        query: str, 
        response: str, 
        wines_recommended: List[Dict] = None,
        session_id: str = None
    ):
        """Guardar conversación en memoria."""
        try:
            wines_json = json.dumps(wines_recommended or [])
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO conversations 
                    (user_id, query, response, wines_recommended, session_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, query, response, wines_json, session_id))
                conn.commit()
            
            logger.info(f"💾 Conversación guardada para usuario {user_id}")
            
        except Exception as e:
            logger.error(f"Error guardando conversación: {e}")
    
    async def get_user_context(self, user_id: str, limit: int = 5) -> Dict[str, Any]:
        """Obtener contexto conversacional del usuario."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Últimas conversaciones
                conversations = conn.execute("""
                    SELECT query, response, wines_recommended, timestamp
                    FROM conversations 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, limit)).fetchall()
                
                # Preferencias
                prefs_row = conn.execute("""
                    SELECT preferences FROM user_preferences 
                    WHERE user_id = ?
                """, (user_id,)).fetchone()
                
                preferences = {}
                if prefs_row:
                    preferences = json.loads(prefs_row['preferences'])
                
                # Vinos mejor valorados
                top_wines = conn.execute("""
                    SELECT wine_name, AVG(rating) as avg_rating, COUNT(*) as count
                    FROM wine_ratings 
                    WHERE user_id = ?
                    GROUP BY wine_name
                    HAVING count >= 1
                    ORDER BY avg_rating DESC, count DESC
                    LIMIT 3
                """, (user_id,)).fetchall()
                
                context = {
                    "user_id": user_id,
                    "recent_conversations": [
                        {
                            "query": conv['query'],
                            "response": conv['response'][:200] + "..." if len(conv['response']) > 200 else conv['response'],
                            "wines": json.loads(conv['wines_recommended']) if conv['wines_recommended'] else [],
                            "timestamp": conv['timestamp']
                        }
                        for conv in conversations
                    ],
                    "preferences": preferences,
                    "favorite_wines": [
                        {
                            "name": wine['wine_name'],
                            "rating": round(wine['avg_rating'], 1),
                            "times_rated": wine['count']
                        }
                        for wine in top_wines
                    ],
                    "total_conversations": len(conversations)
                }
                
                return context
                
        except Exception as e:
            logger.error(f"Error obteniendo contexto de usuario: {e}")
            return {"user_id": user_id, "error": str(e)}
    
    async def update_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Actualizar preferencias del usuario."""
        try:
            prefs_json = json.dumps(preferences)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO user_preferences 
                    (user_id, preferences, last_updated)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (user_id, prefs_json))
                conn.commit()
            
            logger.info(f"✅ Preferencias actualizadas para {user_id}")
            
        except Exception as e:
            logger.error(f"Error actualizando preferencias: {e}")
    
    async def rate_wine(self, user_id: str, wine_name: str, rating: int, notes: str = ""):
        """Guardar valoración de vino."""
        # Validar rating antes de intentar guardar
        if not (1 <= rating <= 5):
            raise ValueError("Rating debe estar entre 1 y 5")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO wine_ratings 
                    (user_id, wine_name, rating, notes)
                    VALUES (?, ?, ?, ?)
                """, (user_id, wine_name, rating, notes))
                conn.commit()
            
            logger.info(f"⭐ Vino '{wine_name}' valorado con {rating}/5 por {user_id}")
            
        except Exception as e:
            logger.error(f"Error guardando valoración: {e}")
            raise  # Re-lanzar la excepción
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la memoria."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                total_conversations = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
                total_users = conn.execute("SELECT COUNT(DISTINCT user_id) FROM conversations").fetchone()[0]
                total_ratings = conn.execute("SELECT COUNT(*) FROM wine_ratings").fetchone()[0]
                
                # Top vinos más consultados
                top_wines = conn.execute("""
                    SELECT wine_name, COUNT(*) as mentions
                    FROM (
                        SELECT json_extract(value, '$.name') as wine_name
                        FROM conversations, json_each(wines_recommended)
                        WHERE wine_name IS NOT NULL
                    )
                    GROUP BY wine_name
                    ORDER BY mentions DESC
                    LIMIT 5
                """).fetchall()
                
                return {
                    "total_conversations": total_conversations,
                    "total_users": total_users,
                    "total_ratings": total_ratings,
                    "top_wines": [{"name": w[0], "mentions": w[1]} for w in top_wines],
                    "database_size": f"{self.db_path.stat().st_size / 1024:.1f} KB"
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {"error": str(e)}

# Instancia global (solo si no estamos en tests)
import os
if os.getenv("ENVIRONMENT") != "test":
    memory = SumillerMemory()
else:
    memory = None  # Se inicializa en los tests 