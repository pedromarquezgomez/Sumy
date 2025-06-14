"""
Configuración global para tests del servicio Agentic RAG
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch

# Configurar variables de entorno para tests
os.environ["ENVIRONMENT"] = "test"
os.environ["USE_EMBEDDED_CHROMA"] = "true"
os.environ["OPENAI_API_KEY"] = "test-key-not-used"
os.environ["LOG_LEVEL"] = "ERROR"

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def event_loop():
    """Crear un event loop para toda la sesión de tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mock_rag_engine():
    """Fixture para crear un motor RAG mockeado"""
    from main import AgenticRAGEngine
    
    engine = AgenticRAGEngine()
    
    # Mock de la inicialización
    engine.vector_db = Mock()
    engine.collection = Mock()
    
    # Mock métodos async
    engine.add_document = AsyncMock(return_value="doc_123")
    engine.semantic_search = AsyncMock(return_value=[])
    engine.agentic_query_expansion = AsyncMock(return_value=["test query"])
    engine.generate_answer = AsyncMock(return_value="Test answer")
    engine.agentic_rag_query = AsyncMock()
    
    return engine

@pytest.fixture
def mock_collection():
    """Fixture para una colección ChromaDB mockeada"""
    collection = Mock()
    collection.get.return_value = {'ids': []}
    collection.add.return_value = None
    collection.query.return_value = {
        'documents': [['Document 1']],
        'metadatas': [[{'source': 'test'}]],
        'distances': [[0.1]]
    }
    return collection 