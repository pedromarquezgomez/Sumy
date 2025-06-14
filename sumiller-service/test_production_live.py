#!/usr/bin/env python3
"""
Tests en vivo contra el servicio Sumiller desplegado en Google Cloud Run
Ejecuta smoke tests y tests de funcionalidad básica
"""
import requests
import json
import time
import sys
from datetime import datetime
import os

# URL del servicio desplegado
SERVICE_URL = os.getenv("SUMILLER_SERVICE_URL", "https://sumiller-service-rkhznukoea-ew.a.run.app")

class ProductionTester:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.test_user_id = f"test_user_{int(time.time())}"
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbol = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
        print(f"[{timestamp}] {symbol.get(level, 'ℹ️')} {message}")
    
    def test_health_check(self):
        """Test 1: Health Check"""
        self.log("Testing health endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            assert data["service"] == "sumiller-service"
            assert "timestamp" in data
            
            self.log(f"Health Status: {data['status']}", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Health check failed: {e}", "ERROR")
            return False
    
    def test_stats_endpoint(self):
        """Test 2: Stats Endpoint"""
        self.log("Testing stats endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/stats", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            assert data["service"] == "sumiller-service"
            assert "wine_database" in data
            
            wine_count = data["wine_database"]["total_wines"]
            self.log(f"Wine Database: {wine_count} wines available", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Stats test failed: {e}", "ERROR")
            return False
    
    def test_query_functionality(self):
        """Test 3: Query Functionality"""
        self.log("Testing query functionality...")
        try:
            query_data = {
                "query": "recomienda un vino tinto para carne asada",
                "user_id": self.test_user_id
            }
            
            response = self.session.post(
                f"{self.base_url}/query",
                json=query_data,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            assert "response" in data
            assert "user_context" in data
            assert data["user_context"]["user_id"] == self.test_user_id
            
            response_length = len(data["response"])
            self.log(f"Query response received ({response_length} chars)", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Query test failed: {e}", "ERROR")
            return False
    
    def test_wine_rating(self):
        """Test 4: Wine Rating"""
        self.log("Testing wine rating functionality...")
        try:
            rating_data = {
                "wine_name": "Test Wine Production",
                "rating": 4,
                "notes": "Test rating from production tests",
                "user_id": self.test_user_id
            }
            
            response = self.session.post(
                f"{self.base_url}/rate-wine",
                json=rating_data,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            assert "message" in data
            
            self.log("Wine rating functionality working", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Wine rating test failed: {e}", "ERROR")
            return False
    
    def test_response_times(self):
        """Test 5: Response Times"""
        self.log("Testing response times...")
        try:
            start_time = time.time()
            
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            
            health_time = time.time() - start_time
            
            # Test query response time
            start_time = time.time()
            query_data = {
                "query": "vino rápido test",
                "user_id": f"speed_test_{int(time.time())}"
            }
            
            response = self.session.post(
                f"{self.base_url}/query",
                json=query_data,
                timeout=15
            )
            response.raise_for_status()
            
            query_time = time.time() - start_time
            
            self.log(f"Health endpoint: {health_time:.2f}s", "SUCCESS")
            self.log(f"Query endpoint: {query_time:.2f}s", "SUCCESS")
            
            if query_time > 30:
                self.log("Query response time is slow (>30s)", "WARNING")
            
            return True
        except Exception as e:
            self.log(f"Response time test failed: {e}", "ERROR")
            return False
    
    def test_user_context_persistence(self):
        """Test 6: User Context Persistence"""
        self.log("Testing user context persistence...")
        try:
            # First query
            query1 = {
                "query": "vino tinto",
                "user_id": self.test_user_id
            }
            
            response1 = self.session.post(
                f"{self.base_url}/query",
                json=query1,
                timeout=20
            )
            response1.raise_for_status()
            
            # Second query to test context
            query2 = {
                "query": "algo más económico",
                "user_id": self.test_user_id
            }
            
            response2 = self.session.post(
                f"{self.base_url}/query",
                json=query2,
                timeout=20
            )
            response2.raise_for_status()
            
            data2 = response2.json()
            context = data2["user_context"]
            
            # Should have conversation history
            conversations = context.get("recent_conversations", [])
            if len(conversations) > 0:
                self.log("User context persistence working", "SUCCESS")
                return True
            else:
                self.log("User context not persisting", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Context persistence test failed: {e}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Execute all production tests"""
        self.log("🚀 STARTING PRODUCTION TESTS")
        self.log(f"Target URL: {self.base_url}")
        self.log(f"Test User ID: {self.test_user_id}")
        print("=" * 60)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Stats Endpoint", self.test_stats_endpoint),
            ("Query Functionality", self.test_query_functionality),
            ("Wine Rating", self.test_wine_rating),
            ("Response Times", self.test_response_times),
            ("Context Persistence", self.test_user_context_persistence),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log(f"Running: {test_name}")
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"Test {test_name} crashed: {e}", "ERROR")
                failed += 1
            
            print("-" * 40)
        
        # Final summary
        print("=" * 60)
        self.log("🎯 PRODUCTION TESTS SUMMARY")
        self.log(f"Passed: {passed}")
        self.log(f"Failed: {failed}")
        
        if failed == 0:
            self.log("🎉 ALL PRODUCTION TESTS PASSED!", "SUCCESS")
            return 0
        else:
            self.log(f"❌ {failed} tests failed", "ERROR")
            return 1

def main():
    """Main function"""
    if len(sys.argv) > 1:
        service_url = sys.argv[1]
    else:
        service_url = SERVICE_URL
    
    if not service_url or service_url == "YOUR_SERVICE_URL_HERE":
        print("❌ Error: Necesitas proporcionar la URL del servicio")
        print("Uso: python3 test_production_live.py <URL_DEL_SERVICIO>")
        print(f"O configurar SUMILLER_SERVICE_URL: export SUMILLER_SERVICE_URL=https://tu-servicio.run.app")
        return 1
    
    tester = ProductionTester(service_url)
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main()) 