"""
Configuración global para los tests del Sumiller Service
"""
import os
import pytest
import tempfile
from pathlib import Path

# Configurar variables de entorno para tests
os.environ["ENVIRONMENT"] = "test"
os.environ["SQLITE_DB_PATH"] = ":memory:"  # Usar SQLite en memoria para tests
os.environ["OPENAI_API_KEY"] = "test-key-not-used-in-tests"
os.environ["LOG_LEVEL"] = "ERROR"  # Reducir logs durante tests

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup del entorno de tests"""
    # Crear directorio temporal para tests
    test_dir = Path("./test_temp")
    test_dir.mkdir(exist_ok=True)
    
    yield
    
    # Cleanup después de todos los tests
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir, ignore_errors=True)

@pytest.fixture
def temp_db_path():
    """Fixture para crear un path de base de datos temporal"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    yield db_path
    
    # Limpiar después del test
    if os.path.exists(db_path):
        os.unlink(db_path) 