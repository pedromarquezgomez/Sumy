"""
Tests de API para el Agentic RAG Service
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Agregar el directorio padre al path para importar main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, rag_engine


class TestHealthEndpoint:
    """Tests para el endpoint de health check"""
    
    def test_health_check(self):
        """Test del endpoint /health"""
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert "service" in data
            assert "timestamp" in data
            assert data["service"] == "agentic-rag-service"


class TestQueryEndpoint:
    """Tests para el endpoint de consultas RAG"""
    
    @pytest.fixture
    def mock_rag_engine(self):
        """Mock del motor RAG para tests"""
        with patch('main.rag_engine') as mock:
            mock.agentic_rag_query = AsyncMock()
            yield mock
    
    def test_query_endpoint_success(self, mock_rag_engine):
        """Test exitoso del endpoint /query"""
        # Mock de respuesta del motor RAG
        from main import RAGResponse
        mock_response = RAGResponse(
            answer="Test answer",
            sources=[{"content": "Test source", "metadata": {}}],
            context_used={}
        )
        mock_rag_engine.agentic_rag_query.return_value = mock_response
        
        with TestClient(app) as client:
            response = client.post(
                "/query",
                json={"query": "test query", "max_results": 5}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "sources" in data
            assert data["answer"] == "Test answer"
    
    def test_query_endpoint_validation_error(self):
        """Test de error de validación en /query"""
        with TestClient(app) as client:
            response = client.post(
                "/query",
                json={"invalid_field": "test"}  # Falta el campo 'query'
            )
            
            assert response.status_code == 422
    
    def test_query_endpoint_empty_query(self):
        """Test con consulta vacía"""
        with TestClient(app) as client:
            response = client.post(
                "/query",
                json={"query": "", "max_results": 5}
            )
            
            assert response.status_code == 400


class TestDocumentsEndpoint:
    """Tests para el endpoint de documentos"""
    
    @pytest.fixture
    def mock_rag_engine(self):
        """Mock del motor RAG para tests"""
        with patch('main.rag_engine') as mock:
            mock.add_document = AsyncMock()
            yield mock
    
    def test_add_document_success(self, mock_rag_engine):
        """Test exitoso de agregar documento"""
        mock_rag_engine.add_document.return_value = "doc_123"
        
        with TestClient(app) as client:
            response = client.post(
                "/documents",
                json={
                    "content": "Test document content",
                    "metadata": {"source": "test"},
                    "doc_id": "test_doc"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "doc_id" in data
            assert "message" in data
            assert data["doc_id"] == "doc_123"
    
    def test_add_document_validation_error(self):
        """Test de error de validación al agregar documento"""
        with TestClient(app) as client:
            response = client.post(
                "/documents",
                json={"invalid_field": "test"}  # Falta el campo 'content'
            )
            
            assert response.status_code == 422
    
    def test_add_document_empty_content(self):
        """Test con contenido vacío"""
        with TestClient(app) as client:
            response = client.post(
                "/documents",
                json={"content": ""}
            )
            
            assert response.status_code == 400


class TestMCPEndpoints:
    """Tests para los endpoints MCP (si están disponibles)"""
    
    def test_mcp_tools_endpoint(self):
        """Test del endpoint de herramientas MCP"""
        with TestClient(app) as client:
            # Este endpoint puede no estar disponible en modo API
            response = client.get("/mcp/tools")
            # Aceptamos tanto 200 como 404 dependiendo de la configuración
            assert response.status_code in [200, 404]
    
    def test_mcp_resources_endpoint(self):
        """Test del endpoint de recursos MCP"""
        with TestClient(app) as client:
            # Este endpoint puede no estar disponible en modo API
            response = client.get("/mcp/resources")
            # Aceptamos tanto 200 como 404 dependiendo de la configuración
            assert response.status_code in [200, 404]


class TestErrorHandling:
    """Tests para manejo de errores"""
    
    @pytest.fixture
    def mock_rag_engine_error(self):
        """Mock del motor RAG que genera errores"""
        with patch('main.rag_engine') as mock:
            mock.agentic_rag_query = AsyncMock(side_effect=Exception("Test error"))
            yield mock
    
    def test_query_endpoint_internal_error(self, mock_rag_engine_error):
        """Test de error interno en /query"""
        with TestClient(app) as client:
            response = client.post(
                "/query",
                json={"query": "test query", "max_results": 5}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data


class TestCORS:
    """Tests para configuración CORS"""
    
    def test_cors_headers(self):
        """Test de headers CORS"""
        with TestClient(app) as client:
            response = client.options("/health")
            # Verificar que no hay errores CORS
            assert response.status_code in [200, 405]  # OPTIONS puede no estar implementado


if __name__ == "__main__":
    pytest.main([__file__]) 