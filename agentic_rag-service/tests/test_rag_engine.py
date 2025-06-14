"""
Tests unitarios para el motor RAG agéntico - REFACTORIZADO
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os

# Configurar entorno de test antes de importar main
os.environ["ENVIRONMENT"] = "test"
os.environ["USE_EMBEDDED_CHROMA"] = "true"
os.environ["OPENAI_API_KEY"] = "test-key-not-used"
os.environ["LOG_LEVEL"] = "ERROR"

# Agregar el directorio padre al path para importar main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import AgenticRAGEngine, QueryRequest, DocumentRequest


class TestAgenticRAGEngine:
    """Tests para el motor RAG agéntico"""
    
    def test_rag_engine_initialization(self):
        """Test de inicialización del motor RAG"""
        engine = AgenticRAGEngine()
        assert engine is not None
        assert hasattr(engine, 'embedding_model')
        assert hasattr(engine, 'vector_db')
        assert hasattr(engine, 'collection')
        assert hasattr(engine, 'openai_client')
    
    def test_embed_text(self):
        """Test de generación de embeddings - CORREGIDO"""
        engine = AgenticRAGEngine()
        
        # Mock del modelo de embedding
        with patch.object(engine.embedding_model, 'encode') as mock_encode:
            # Configurar el mock para que devuelva un objeto con método tolist()
            mock_result = Mock()
            mock_result.tolist.return_value = [0.1, 0.2, 0.3]
            mock_encode.return_value = mock_result
            
            result = engine._embed_text("test text")
            
            assert result == [0.1, 0.2, 0.3]
            mock_encode.assert_called_once_with("test text")
    
    @pytest.mark.asyncio
    async def test_add_document(self):
        """Test de agregar documento - CORREGIDO"""
        engine = AgenticRAGEngine()
        
        # Mock de la colección
        mock_collection = Mock()
        mock_collection.get.return_value = {'ids': []}
        mock_collection.add.return_value = None
        engine.collection = mock_collection
        
        # Mock del método de embedding
        with patch.object(engine, '_embed_text') as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]
            
            doc_id = await engine.add_document(
                content="Test document",
                metadata={"source": "test"}
            )
            
            assert doc_id == "doc_1"
            mock_collection.add.assert_called_once()
            mock_embed.assert_called_once_with("Test document")
    
    @pytest.mark.asyncio
    async def test_add_document_with_custom_id(self):
        """Test de agregar documento con ID personalizado"""
        engine = AgenticRAGEngine()
        
        # Mock de la colección
        mock_collection = Mock()
        mock_collection.get.return_value = {'ids': []}
        mock_collection.add.return_value = None
        engine.collection = mock_collection
        
        # Mock del método de embedding
        with patch.object(engine, '_embed_text') as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]
            
            doc_id = await engine.add_document(
                content="Test document",
                metadata={"source": "test"},
                doc_id="custom_doc_id"
            )
            
            assert doc_id == "custom_doc_id"
            mock_collection.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_semantic_search(self):
        """Test de búsqueda semántica - CORREGIDO"""
        engine = AgenticRAGEngine()
        
        # Mock de la colección
        mock_collection = Mock()
        mock_results = {
            'documents': [['Document 1', 'Document 2']],
            'metadatas': [[{'source': 'test1'}, {'source': 'test2'}]],
            'distances': [[0.1, 0.2]]
        }
        mock_collection.query.return_value = mock_results
        engine.collection = mock_collection
        
        # Mock del método de embedding
        with patch.object(engine, '_embed_text') as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]
            
            results = await engine.semantic_search("test query", max_results=2)
            
            assert len(results) == 2
            assert results[0]['content'] == 'Document 1'
            assert results[0]['relevance_score'] == 0.9  # 1 - 0.1
            assert results[0]['rank'] == 1
            assert results[1]['content'] == 'Document 2'
            assert results[1]['relevance_score'] == 0.8  # 1 - 0.2
            assert results[1]['rank'] == 2
    
    @pytest.mark.asyncio
    async def test_semantic_search_empty_results(self):
        """Test de búsqueda semántica sin resultados"""
        engine = AgenticRAGEngine()
        
        # Mock de la colección con resultados vacíos
        mock_collection = Mock()
        mock_results = {
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]]
        }
        mock_collection.query.return_value = mock_results
        engine.collection = mock_collection
        
        # Mock del método de embedding
        with patch.object(engine, '_embed_text') as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]
            
            results = await engine.semantic_search("test query")
            
            assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_agentic_query_expansion_without_openai(self):
        """Test de expansión de consulta sin OpenAI"""
        engine = AgenticRAGEngine()
        engine.openai_client = None
        
        result = await engine.agentic_query_expansion("test query")
        
        assert result == ["test query"]
    
    @pytest.mark.asyncio
    async def test_agentic_query_expansion_with_openai(self):
        """Test de expansión de consulta con OpenAI - CORREGIDO"""
        engine = AgenticRAGEngine()
        
        # Mock del cliente OpenAI
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = '["expanded query 1", "expanded query 2"]'
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        engine.openai_client = mock_client
        
        # Mock json.loads en el módulo main para parsear la respuesta
        with patch('main.json.loads') as mock_loads:
            mock_loads.return_value = ["expanded query 1", "expanded query 2"]
            
            result = await engine.agentic_query_expansion("test query")
            
            # El método real devuelve [query_original] + expansiones
            assert result == ["test query", "expanded query 1", "expanded query 2"]
            mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_answer_without_openai(self):
        """Test de generación de respuesta sin OpenAI"""
        engine = AgenticRAGEngine()
        engine.openai_client = None
        
        sources = [{'content': 'Test doc', 'metadata': {}}]
        result = await engine.generate_answer("test query", sources)
        
        assert "Basado en 1 fuentes encontradas" in result
        assert "test query" in result
    
    @pytest.mark.asyncio
    async def test_generate_answer_with_openai(self):
        """Test de generación de respuesta con OpenAI - CORREGIDO"""
        engine = AgenticRAGEngine()
        
        # Mock del cliente OpenAI
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Generated answer from OpenAI"
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        engine.openai_client = mock_client
        
        sources = [{'content': 'Test doc', 'metadata': {}}]
        result = await engine.generate_answer("test query", sources)
        
        assert result == "Generated answer from OpenAI"
        mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_agentic_rag_query_complete(self):
        """Test de consulta RAG agéntica completa - CORREGIDO"""
        engine = AgenticRAGEngine()
        
        # Mock de métodos internos
        with patch.object(engine, 'agentic_query_expansion') as mock_expand, \
             patch.object(engine, 'semantic_search') as mock_search, \
             patch.object(engine, 'generate_answer') as mock_generate:
            
            mock_expand.return_value = ["test query", "expanded query"]
            mock_search.return_value = [
                {'content': 'Test doc', 'metadata': {}, 'relevance_score': 0.9}
            ]
            mock_generate.return_value = "Generated answer"
            
            result = await engine.agentic_rag_query("test query")
            
            assert result.answer == "Generated answer"
            assert len(result.sources) == 1
            assert result.sources[0]['content'] == 'Test doc'
            # El método real devuelve context or {} por defecto
            assert result.context_used == {}
    
    @pytest.mark.asyncio
    async def test_initialize_with_embedded_chroma(self):
        """Test de inicialización con ChromaDB embebido"""
        engine = AgenticRAGEngine()
        
        # Mock de ChromaDB
        with patch('main.chromadb.EphemeralClient') as mock_client:
            mock_db = Mock()
            mock_collection = Mock()
            mock_db.create_collection.return_value = mock_collection
            mock_client.return_value = mock_db
            
            await engine.initialize()
            
            assert engine.vector_db is not None
            assert engine.collection is not None
            mock_client.assert_called_once()


class TestDataModels:
    """Tests para los modelos de datos"""
    
    def test_query_request_model(self):
        """Test del modelo QueryRequest"""
        request = QueryRequest(query="test query", max_results=10)
        assert request.query == "test query"
        assert request.max_results == 10
        assert request.context is None
    
    def test_query_request_with_context(self):
        """Test del modelo QueryRequest con contexto"""
        context = {"user": "test_user", "session": "abc123"}
        request = QueryRequest(
            query="test query",
            context=context,
            max_results=5
        )
        assert request.query == "test query"
        assert request.context == context
        assert request.max_results == 5
    
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
    
    def test_document_request_minimal(self):
        """Test del modelo DocumentRequest con campos mínimos"""
        request = DocumentRequest(content="test content")
        assert request.content == "test content"
        assert request.metadata is None
        assert request.doc_id is None


class TestErrorHandling:
    """Tests para manejo de errores en el motor RAG"""
    
    @pytest.mark.asyncio
    async def test_add_document_error(self):
        """Test de error al agregar documento"""
        engine = AgenticRAGEngine()
        
        # Mock de la colección que falla
        mock_collection = Mock()
        mock_collection.get.return_value = {'ids': []}  # Necesario para el cálculo de doc_id
        mock_collection.add.side_effect = Exception("Database error")
        engine.collection = mock_collection
        
        # Mock del método de embedding
        with patch.object(engine, '_embed_text') as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]
            
            with pytest.raises(Exception) as exc_info:
                await engine.add_document("test content")
            
            assert "Database error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_semantic_search_error(self):
        """Test de error en búsqueda semántica"""
        engine = AgenticRAGEngine()
        
        # Mock de la colección que falla
        mock_collection = Mock()
        mock_collection.query.side_effect = Exception("Search error")
        engine.collection = mock_collection
        
        # Mock del método de embedding
        with patch.object(engine, '_embed_text') as mock_embed:
            mock_embed.return_value = [0.1, 0.2, 0.3]
            
            results = await engine.semantic_search("test query")
            
            # Debería devolver lista vacía en caso de error
            assert results == []


if __name__ == "__main__":
    pytest.main([__file__]) 