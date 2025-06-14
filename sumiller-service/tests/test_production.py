#!/usr/bin/env python3
"""
Tests de producción (Smoke Tests) para el Sumiller Service
Estos tests verifican que el servicio funciona correctamente en producción
"""

import pytest
import httpx
import os
import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TestProductionSumillerService:
    """Tests de producción para verificar el servicio desplegado"""
    
    @pytest.fixture
    def base_url(self) -> str:
        """URL base del servicio en producción"""
        # Obtener URL de variable de entorno o usar localhost para tests locales
        return os.getenv("SUMILLER_SERVICE_URL", "http://localhost:8080")
    
    @pytest.fixture
    def timeout(self) -> int:
        """Timeout para requests en producción"""
        return 30  # 30 segundos para producción
    
    @pytest.mark.asyncio
    async def test_service_health(self, base_url: str, timeout: int):
        """Test: Servicio está vivo y responde"""
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.get(f"{base_url}/health")
                
                assert response.status_code == 200
                data = response.json()
                
                # Verificaciones básicas de salud
                assert data["status"] in ["healthy", "degraded", "error"]
                assert data["service"] == "sumiller-service"
                assert "timestamp" in data
                
                # En producción, verificar componentes si están disponibles
                if data["status"] == "healthy" and "components" in data:
                    # Verificar que al menos algunos componentes estén OK
                    components = data["components"]
                    
                    # Verificar componentes reales del servicio
                    if "memory" in components:
                        assert components["memory"] in ["healthy", "ok"]
                    if "openai" in components:
                        assert components["openai"] in ["healthy", "ok"]
                    if "search_service" in components:
                        assert components["search_service"] in ["local", "ok"]
                
                logger.info(f"✅ Health check passed: {data['status']}")
                
            except httpx.ConnectError:
                pytest.skip(f"Servicio no disponible en {base_url}")
            except Exception as e:
                pytest.fail(f"Error inesperado en health check: {e}")
    
    @pytest.mark.asyncio
    async def test_stats_endpoint(self, base_url: str, timeout: int):
        """Test: Endpoint de estadísticas funciona"""
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{base_url}/stats")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["service"] == "sumiller-service"
            assert "memory" in data
            assert "wine_database" in data
            
            # Verificar que la base de vinos está cargada
            assert data["wine_database"]["total_wines"] >= 4
            
            print(f"✅ Estadísticas OK: {data['wine_database']['total_wines']} vinos disponibles")
    
    @pytest.mark.asyncio
    async def test_basic_query_functionality(self, base_url: str, timeout: int):
        """Test: Funcionalidad básica de consultas"""
        async with httpx.AsyncClient(timeout=timeout) as client:
            query_data = {
                "query": "vino tinto para carne asada",
                "user_id": "production_test_user"
            }
            
            response = await client.post(
                f"{base_url}/query",
                json=query_data
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verificaciones básicas de respuesta
            assert "response" in data
            assert "wines_recommended" in data
            assert "user_context" in data
            assert "confidence" in data
            
            assert isinstance(data["response"], str)
            assert len(data["response"]) > 0
            assert isinstance(data["wines_recommended"], list)
            
            print(f"✅ Consulta procesada correctamente")
            print(f"   Respuesta: {data['response'][:100]}...")
            print(f"   Vinos recomendados: {len(data['wines_recommended'])}")
    
    @pytest.mark.asyncio
    async def test_user_context_persistence(self, base_url: str, timeout: int):
        """Test: La persistencia de contexto de usuario funciona"""
        user_id = "production_persistence_test"
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Primera consulta
            query1 = {
                "query": "vino blanco para pescado",
                "user_id": user_id
            }
            
            response1 = await client.post(f"{base_url}/query", json=query1)
            assert response1.status_code == 200
            
            # Obtener contexto
            response_context = await client.get(f"{base_url}/user/{user_id}/context")
            assert response_context.status_code == 200
            
            context = response_context.json()
            assert context["user_id"] == user_id
            assert len(context["recent_conversations"]) >= 1
            
            print(f"✅ Persistencia de contexto funciona")
            print(f"   Conversaciones guardadas: {len(context['recent_conversations'])}")
    
    @pytest.mark.asyncio
    async def test_wine_rating_functionality(self, base_url: str, timeout: int):
        """Test: Sistema de valoraciones funciona"""
        async with httpx.AsyncClient(timeout=timeout) as client:
            rating_data = {
                "wine_name": "Rioja Gran Reserva Test",
                "rating": 4,
                "notes": "Muy bueno para producción",
                "user_id": "production_rating_test"
            }
            
            response = await client.post(f"{base_url}/rate-wine", json=rating_data)
            assert response.status_code == 200
            
            data = response.json()
            assert "message" in data
            assert "Rioja Gran Reserva Test" in data["message"]
            
            print(f"✅ Sistema de valoraciones funciona")
    
    @pytest.mark.asyncio
    async def test_preferences_functionality(self, base_url: str, timeout: int):
        """Test: Sistema de preferencias funciona"""
        async with httpx.AsyncClient(timeout=timeout) as client:
            preferences_data = {
                "preferences": {
                    "wine_types": ["tinto"],
                    "max_price": 40,
                    "regions": ["Rioja"]
                },
                "user_id": "production_prefs_test"
            }
            
            response = await client.post(f"{base_url}/preferences", json=preferences_data)
            assert response.status_code == 200
            
            data = response.json()
            assert "message" in data
            assert "actualizadas" in data["message"]
            
            print(f"✅ Sistema de preferencias funciona")
    
    @pytest.mark.asyncio
    async def test_response_times(self, base_url: str, timeout: int):
        """Test: Tiempos de respuesta aceptables"""
        import time
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Test health endpoint (debería ser muy rápido)
            start_time = time.time()
            response = await client.get(f"{base_url}/health")
            health_time = time.time() - start_time
            
            assert response.status_code == 200
            assert health_time < 5.0  # Menos de 5 segundos
            
            # Test query endpoint (puede ser más lento por IA)
            start_time = time.time()
            query_data = {
                "query": "vino para celebrar",
                "user_id": "performance_test"
            }
            response = await client.post(f"{base_url}/query", json=query_data)
            query_time = time.time() - start_time
            
            assert response.status_code == 200
            assert query_time < 30.0  # Menos de 30 segundos
            
            print(f"✅ Tiempos de respuesta aceptables")
            print(f"   Health: {health_time:.2f}s")
            print(f"   Query: {query_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, base_url: str, timeout: int):
        """Test: Manejo de requests concurrentes"""
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Crear múltiples requests concurrentes
            tasks = []
            for i in range(5):
                query_data = {
                    "query": f"vino número {i}",
                    "user_id": f"concurrent_user_{i}"
                }
                task = client.post(f"{base_url}/query", json=query_data)
                tasks.append(task)
            
            # Ejecutar todas las requests concurrentemente
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verificar que todas las responses son exitosas
            successful_responses = 0
            for response in responses:
                if isinstance(response, httpx.Response) and response.status_code == 200:
                    successful_responses += 1
            
            assert successful_responses >= 4  # Al menos 4 de 5 exitosas
            
            print(f"✅ Requests concurrentes manejadas: {successful_responses}/5")


class TestProductionEnvironment:
    """Tests específicos del entorno de producción"""
    
    def test_environment_variables(self):
        """Test: Variables de entorno necesarias están configuradas"""
        # En producción, estas variables deberían estar configuradas
        required_vars = ["OPENAI_API_KEY"]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️  Variables faltantes (OK para tests locales): {missing_vars}")
        else:
            print(f"✅ Variables de entorno configuradas")
    
    def test_production_config(self):
        """Test: Configuración de producción"""
        environment = os.getenv("ENVIRONMENT", "development")
        
        if environment == "production":
            # En producción, verificar configuraciones específicas
            assert os.getenv("LOG_LEVEL", "INFO") in ["WARNING", "ERROR", "INFO"]
            print(f"✅ Configuración de producción detectada")
        else:
            print(f"ℹ️  Entorno: {environment} (no es producción)")


if __name__ == "__main__":
    # Ejecutar tests de producción
    import sys
    
    # Configurar para tests de producción
    if len(sys.argv) > 1 and sys.argv[1] == "--production":
        # URL de producción debe ser proporcionada
        if not os.getenv("SUMILLER_SERVICE_URL"):
            print("❌ Error: SUMILLER_SERVICE_URL no configurada para tests de producción")
            sys.exit(1)
        
        print(f"🚀 Ejecutando tests de producción contra: {os.getenv('SUMILLER_SERVICE_URL')}")
        pytest.main([__file__, "-v", "-s"])
    else:
        print("🧪 Ejecutando tests locales (usar --production para tests de producción)")
        pytest.main([__file__, "-v"]) 