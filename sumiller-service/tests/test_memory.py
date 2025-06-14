#!/usr/bin/env python3
"""
Tests unitarios para el módulo de memoria SQLite
"""

import pytest
import tempfile
import os
from pathlib import Path
import asyncio

# Importar el módulo a testear
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from memory import SumillerMemory


class TestSumillerMemory:
    """Tests para la clase SumillerMemory"""
    
    @pytest.fixture
    def temp_db(self):
        """Crear base de datos temporal para tests"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        # Crear instancia con DB temporal
        memory = SumillerMemory(db_path=db_path)
        yield memory
        
        # Limpiar después del test
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_database_initialization(self, temp_db):
        """Test: La base de datos se inicializa correctamente"""
        assert temp_db.db_path.exists()
        
        # Verificar que las tablas existen
        import sqlite3
        with sqlite3.connect(temp_db.db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar tabla conversations
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'")
            assert cursor.fetchone() is not None
            
            # Verificar tabla user_preferences
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_preferences'")
            assert cursor.fetchone() is not None
            
            # Verificar tabla wine_ratings
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wine_ratings'")
            assert cursor.fetchone() is not None
    
    @pytest.mark.asyncio
    async def test_save_conversation(self, temp_db):
        """Test: Guardar conversación funciona correctamente"""
        user_id = "test_user"
        query = "¿Qué vino recomiendas?"
        response = "Te recomiendo un Rioja"
        wines = [{"name": "Rioja", "price": 25.0}]
        
        await temp_db.save_conversation(user_id, query, response, wines)
        
        # Verificar que se guardó
        context = await temp_db.get_user_context(user_id)
        assert context["user_id"] == user_id
        assert context["total_conversations"] == 1
        assert len(context["recent_conversations"]) == 1
        assert context["recent_conversations"][0]["query"] == query
    
    @pytest.mark.asyncio
    async def test_user_preferences(self, temp_db):
        """Test: Gestión de preferencias de usuario"""
        user_id = "test_user"
        preferences = {
            "wine_types": ["tinto", "blanco"],
            "max_price": 30,
            "regions": ["Rioja", "Ribera del Duero"]
        }
        
        # Guardar preferencias
        await temp_db.update_preferences(user_id, preferences)
        
        # Obtener contexto y verificar
        context = await temp_db.get_user_context(user_id)
        assert context["preferences"] == preferences
    
    @pytest.mark.asyncio
    async def test_wine_ratings(self, temp_db):
        """Test: Sistema de valoraciones de vinos"""
        user_id = "test_user"
        wine_name = "Rioja Gran Reserva"
        rating = 5
        notes = "Excelente vino"
        
        # Guardar valoración
        await temp_db.rate_wine(user_id, wine_name, rating, notes)
        
        # Verificar en contexto
        context = await temp_db.get_user_context(user_id)
        assert len(context["favorite_wines"]) == 1
        assert context["favorite_wines"][0]["name"] == wine_name
        assert context["favorite_wines"][0]["rating"] == rating
    
    @pytest.mark.asyncio
    async def test_invalid_rating(self, temp_db):
        """Test: Validación de ratings inválidos"""
        user_id = "test_user"
        wine_name = "Test Wine"
        
        # Rating inválido (fuera del rango 1-5)
        with pytest.raises(ValueError):
            await temp_db.rate_wine(user_id, wine_name, 6, "")
        
        with pytest.raises(ValueError):
            await temp_db.rate_wine(user_id, wine_name, 0, "")
    
    @pytest.mark.asyncio
    async def test_multiple_conversations(self, temp_db):
        """Test: Múltiples conversaciones y límite de contexto"""
        user_id = "test_user"
        
        # Guardar múltiples conversaciones
        for i in range(10):
            await temp_db.save_conversation(
                user_id, 
                f"Query {i}", 
                f"Response {i}", 
                [{"name": f"Wine {i}"}]
            )
        
        # Verificar que solo se devuelven las últimas 5 (límite por defecto)
        context = await temp_db.get_user_context(user_id, limit=5)
        assert len(context["recent_conversations"]) == 5
        assert context["total_conversations"] == 5  # Solo las que se muestran
        
        # Verificar que tenemos conversaciones válidas
        queries = [conv["query"] for conv in context["recent_conversations"]]
        assert len(queries) == 5
        
        # Todas las queries deben seguir el patrón "Query X"
        for query in queries:
            assert query.startswith("Query ")
            
        # Verificar que tenemos diferentes queries (no duplicadas)
        assert len(set(queries)) >= 3  # Al menos 3 queries diferentes
    
    @pytest.mark.asyncio
    async def test_stats(self, temp_db):
        """Test: Estadísticas del sistema"""
        # Agregar algunos datos
        await temp_db.save_conversation("user1", "query1", "response1", [])
        await temp_db.save_conversation("user2", "query2", "response2", [])
        await temp_db.rate_wine("user1", "Wine1", 5, "")
        
        stats = await temp_db.get_stats()
        
        assert stats["total_conversations"] == 2
        assert stats["total_users"] == 2
        assert stats["total_ratings"] == 1
        assert "database_size" in stats
    
    @pytest.mark.asyncio
    async def test_empty_context(self, temp_db):
        """Test: Contexto de usuario sin datos"""
        context = await temp_db.get_user_context("new_user")
        
        assert context["user_id"] == "new_user"
        assert context["recent_conversations"] == []
        assert context["preferences"] == {}
        assert context["favorite_wines"] == []
        assert context["total_conversations"] == 0


if __name__ == "__main__":
    # Ejecutar tests directamente
    pytest.main([__file__, "-v"]) 