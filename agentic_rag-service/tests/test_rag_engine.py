"""
Tests unitarios para el motor RAG agéntico
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Agregar el directorio padre al path para importar main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import AgenticRAGEngine, QueryRequest, DocumentRequest


class TestAgenticRAGEngine:
    """Tests para el motor RAG agéntico"""
    
    @pytest.fixture
    async def rag_engine(self):
        """Fixture para crear una instancia del motor RAG"""
        engine = AgenticRAGEngine()
        # Mock de la inicialización para evitar dependencias externas
        with patch.object(engine, 'initialize') as mock_init:
            mock_init.return_value = None
            await engine.initialize()
        return engine
    
    def test_rag_engine_initialization(self):
        """Test de inicialización del motor RAG"""
        engine = AgenticRAGEngine()
        assert engine is not None
        assert hasattr(engine, 'embedding_model')
        assert hasattr(engine, 'vector_db')
        assert hasattr(engine, 'collection')
    
    @pytest.mark.asyncio
    async def test_embed_text(self, rag_engine):
        """Test de generación de embeddings"""
        with patch.object(rag_engine.embedding_model, 'encode') as mock_encode:
            mock_encode.return_value.tolist.return_value = [0.1, 0.2, 0.3]
            
            result = rag_engine._embed_text("test text")
            
            assert result == [0.1, 0.2, 0.3]
            mock_encode.assert_called_once_with("test text")
    
    @pytest.mark.asyncio
    async def test_add_document(self, rag_engine):
        """Test de agregar documento"""
        # Mock de la colección
        mock_collection = Mock()
        rag_engine.collection = mock_collection
        
        with patch.object(rag_engine, '_embed_text') as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]
            mock_collection.get.return_value = {'ids': []}
            
            doc_id = await rag_engine.add_document(
                content="Test document",
                metadata={"source": "test"}
            )
            
            assert doc_id == "doc_1"
            mock_collection.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_semantic_search(self, rag_engine):
        """Test de búsqueda semántica"""
        # Mock de la colección
        mock_collection = Mock()
        rag_engine.collection = mock_collection
        
        # Mock de resultados de búsqueda
        mock_results = {
            'documents': [['Document 1', 'Document 2']],
            'metadatas': [[{'source': 'test1'}, {'source': 'test2'}]],
            'distances': [[0.1, 0.2]]
        }
        mock_collection.query.return_value = mock_results
        
        with patch.object(rag_engine, '_embed_text') as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]
            
            results = await rag_engine.semantic_search("test query")
            
            assert len(results) == 2
            assert results[0]['content'] == 'Document 1'
            assert results[0]['relevance_score'] == 0.9  # 1 - 0.1
            assert results[1]['content'] == 'Document 2'
            assert results[1]['relevance_score'] == 0.8  # 1 - 0.2
    
    @pytest.mark.asyncio
    async def test_agentic_query_expansion_without_openai(self, rag_engine):
        """Test de expansión de consulta sin OpenAI"""
        rag_engine.openai_client = None
        
        result = await rag_engine.agentic_query_expansion("test query")
        
        assert result == ["test query"]
    
    @pytest.mark.asyncio
    async def test_agentic_rag_query(self, rag_engine):
        """Test de consulta RAG agéntica completa"""
        # Mock de métodos internos
        with patch.object(rag_engine, 'agentic_query_expansion') as mock_expand, \
             patch.object(rag_engine, 'semantic_search') as mock_search, \
             patch.object(rag_engine, 'generate_answer') as mock_generate:
            
            mock_expand.return_value = ["expanded query"]
            mock_search.return_value = [
                {'content': 'Test doc', 'metadata': {}, 'relevance_score': 0.9}
            ]
            mock_generate.return_value = "Generated answer"
            
            result = await rag_engine.agentic_rag_query("test query")
            
            assert result.answer == "Generated answer"
            assert len(result.sources) == 1
            assert result.sources[0]['content'] == 'Test doc'


class TestDataModels:
    """Tests para los modelos de datos"""
    
    def test_query_request_model(self):
        """Test del modelo QueryRequest"""
        request = QueryRequest(query="test query", max_results=10)
        assert request.query == "test query"
        assert request.max_results == 10
        assert request.context is None
    
    def test_document_request_model(self):
        """Test del modelo DocumentRequest"""
        request = DocumentRequest(
            content="test content",
            metadata={"source": "test"},
            doc_id="test_id"
        )
        assert request.content == "test content"
        assert request.metadata == {"source": "test"}
        assert request.doc_id == "test_id"


if __name__ == "__main__":
    pytest.main([__file__]) 