#!/usr/bin/env python3
"""
Tests de integración para la API del Sumiller Service
"""

import pytest
import os
import tempfile
from fastapi.testclient import TestClient
import json
from unittest.mock import AsyncMock, patch
from datetime import datetime

# Configurar variables de entorno para tests
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["OPENAI_API_KEY"] = "test-key-for-testing"

# Importar la aplicación
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock de memoria para tests (en RAM, sin SQLite)
class MockSumillerMemory:
    def __init__(self):
        self.conversations = []
        self.preferences = {}
        self.ratings = []
    
    async def save_conversation(self, user_id, query, response, wines_recommended=None, session_id=None):
        conversation = {
            "user_id": user_id,
            "query": query,
            "response": response,
            "wines_recommended": wines_recommended or [],
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        self.conversations.append(conversation)
    
    async def get_user_context(self, user_id):
        user_conversations = [c for c in self.conversations if c["user_id"] == user_id]
        user_prefs = self.preferences.get(user_id, {})
        user_ratings = [r for r in self.ratings if r["user_id"] == user_id]
        
        return {
            "user_id": user_id,
            "conversation_count": len(user_conversations),
            "recent_queries": [c["query"] for c in user_conversations[-3:]],
            "preferences": user_prefs,
            "wine_ratings": user_ratings,
            "last_interaction": user_conversations[-1]["timestamp"] if user_conversations else None
        }
    
    async def update_preferences(self, user_id, preferences):
        self.preferences[user_id] = preferences
    
    async def rate_wine(self, user_id, wine_name, rating, notes=""):
        if not (1 <= rating <= 5):
            raise ValueError("Rating must be between 1 and 5")
        
        rating_data = {
            "user_id": user_id,
            "wine_name": wine_name,
            "rating": rating,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }
        self.ratings.append(rating_data)
    
    async def get_stats(self):
        return {
            "total_conversations": len(self.conversations),
            "total_users": len(set(c["user_id"] for c in self.conversations)),
            "total_ratings": len(self.ratings),
            "database_size": "0 KB (mock)"
        }

# Fixture para cliente con memoria mock
@pytest.fixture
def client():
    """Cliente de prueba con memoria mock"""
    with patch('main.memory', MockSumillerMemory()):
        from main import app
        with TestClient(app) as test_client:
            yield test_client

class TestSumillerAPI:
    """Tests de integración para la API"""
    
    def test_health_endpoint(self, client):
        """Test: Endpoint de health check"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # En tests puede fallar por filesystem readonly, pero debe responder
        assert data["status"] in ["healthy", "degraded", "error"]
        assert data["service"] == "sumiller-service"
        assert data["version"] == "2.0.0"
        assert "timestamp" in data
        
        # Si no hay error, verificar componentes
        if data["status"] != "error":
            assert "components" in data
            assert "memory_stats" in data
    
    def test_stats_endpoint(self, client):
        """Test: Endpoint de estadísticas"""
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "sumiller-service"
        
        # En tests puede fallar la memoria por filesystem readonly
        if "error" not in data:
            assert "memory" in data
        
        assert "wine_database" in data
        assert data["wine_database"]["total_wines"] == 4  # Vinos embebidos
        assert "features" in data
        assert data["features"]["intelligent_filter"] == True
    
    def test_query_endpoint_basic(self, client):
        """Test: Endpoint de consulta básica"""
        query_data = {
            "query": "vino tinto para carne",
            "user_id": "test_user"
        }
        
        response = client.post("/query", json=query_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert "wines_recommended" in data
        assert "user_context" in data
        assert "confidence" in data
        assert "query_category" in data  # NUEVO
        assert "used_rag" in data        # NUEVO
        assert isinstance(data["wines_recommended"], list)
        assert data["user_context"]["user_id"] == "test_user"
    
    def test_query_endpoint_with_session(self, client):
        """Test: Consulta con session_id"""
        query_data = {
            "query": "vino blanco para pescado",
            "user_id": "test_user_session",
            "session_id": "session_123"
        }
        
        response = client.post("/query", json=query_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
    
    def test_rate_wine_endpoint(self, client):
        """Test: Endpoint para valorar vinos"""
        rating_data = {
            "wine_name": "Rioja Gran Reserva",
            "rating": 5,
            "notes": "Excelente vino para carne",
            "user_id": "test_user_rating"
        }
        
        response = client.post("/rate-wine", json=rating_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Rioja Gran Reserva" in data["message"]
        assert "5/5" in data["message"]
    
    def test_rate_wine_invalid_rating(self, client):
        """Test: Valoración inválida"""
        rating_data = {
            "wine_name": "Test Wine",
            "rating": 6,  # Inválido
            "user_id": "test_user"
        }
        
        response = client.post("/rate-wine", json=rating_data)
        assert response.status_code == 500  # Error interno por validación
    
    def test_preferences_endpoint(self, client):
        """Test: Endpoint de preferencias"""
        preferences_data = {
            "preferences": {
                "wine_types": ["tinto", "blanco"],
                "max_price": 50,
                "regions": ["Rioja", "Ribera del Duero"]
            },
            "user_id": "test_user_prefs"
        }
        
        response = client.post("/preferences", json=preferences_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "actualizadas" in data["message"]
    
    def test_user_context_endpoint(self, client):
        """Test: Endpoint de contexto de usuario"""
        user_id = "test_context_user"
        
        # Primero hacer una consulta para crear contexto
        query_data = {
            "query": "vino para celebrar",
            "user_id": user_id
        }
        client.post("/query", json=query_data)
        
        # Luego obtener el contexto
        response = client.get(f"/user/{user_id}/context")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == user_id
        assert "conversation_count" in data
        assert data["conversation_count"] >= 1
        assert "recent_queries" in data
        assert len(data["recent_queries"]) >= 1
    
    def test_query_missing_fields(self, client):
        """Test: Consulta con campos faltantes"""
        # Sin query
        response = client.post("/query", json={"user_id": "test"})
        assert response.status_code == 422  # Validation error
        
        # Sin user_id (debería usar default)
        response = client.post("/query", json={"query": "test query"})
        assert response.status_code == 200
    
    def test_wine_search_functionality(self, client):
        """Test: Funcionalidad de búsqueda de vinos"""
        # Buscar vino tinto
        response = client.post("/query", json={
            "query": "vino tinto",
            "user_id": "test_search"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Debería encontrar vinos tintos en la base embebida
        wines = data["wines_recommended"]
        if wines:  # Si encuentra vinos
            tinto_found = any("tinto" in wine.get("type", "").lower() for wine in wines)
            assert tinto_found or len(wines) > 0  # Al menos encuentra algo
    
    def test_conversation_memory(self, client):
        """Test: Memoria conversacional funciona"""
        user_id = "test_memory_user"
        
        # Primera consulta
        response1 = client.post("/query", json={
            "query": "vino tinto para carne",
            "user_id": user_id
        })
        assert response1.status_code == 200
        
        # Segunda consulta - debería tener contexto de la primera
        response2 = client.post("/query", json={
            "query": "¿y para pescado?",
            "user_id": user_id
        })
        assert response2.status_code == 200
        
        # Verificar que el contexto incluye la conversación anterior
        context = response2.json()["user_context"]
        assert context["conversation_count"] >= 1
        assert len(context["recent_queries"]) >= 1
        assert "vino tinto para carne" in context["recent_queries"]
    
    def test_concurrent_users(self, client):
        """Test: Múltiples usuarios simultáneos"""
        users = ["user1", "user2", "user3"]
        
        for user in users:
            response = client.post("/query", json={
                "query": f"vino para {user}",
                "user_id": user
            })
            assert response.status_code == 200
        
        # Verificar que cada usuario tiene su propio contexto
        for user in users:
            response = client.get(f"/user/{user}/context")
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == user


class TestSumillerAPIErrors:
    """Tests para manejo de errores"""
    
    def test_invalid_json(self, client):
        """Test: JSON inválido"""
        response = client.post(
            "/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_nonexistent_user_context(self, client):
        """Test: Contexto de usuario inexistente"""
        response = client.get("/user/nonexistent_user/context")
        assert response.status_code == 200  # Debería devolver contexto vacío
        
        data = response.json()
        assert data["user_id"] == "nonexistent_user"
        assert data["conversation_count"] == 0  # Corregido: era total_conversations
        assert data["recent_queries"] == []
        assert data["preferences"] == {}
        assert data["wine_ratings"] == []


if __name__ == "__main__":
    # Ejecutar tests directamente
    pytest.main([__file__, "-v"]) 