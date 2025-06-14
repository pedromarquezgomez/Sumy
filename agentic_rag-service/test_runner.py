#!/usr/bin/env python3
"""
Test Runner para Agentic RAG Service
Ejecuta tests de manera controlada con configuración específica
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def setup_test_environment():
    """Configurar variables de entorno para tests"""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["USE_EMBEDDED_CHROMA"] = "true"
    os.environ["OPENAI_API_KEY"] = "test-key-not-used"
    os.environ["LOG_LEVEL"] = "ERROR"
    os.environ["PYTHONPATH"] = str(Path(__file__).parent)
    
    print("✅ Entorno de tests configurado")

def run_tests(test_file=None, verbose=False, coverage=False):
    """Ejecutar tests con pytest"""
    cmd = ["python3", "-m", "pytest"]
    
    if test_file:
        cmd.append(f"tests/{test_file}")
    else:
        cmd.append("tests/")
    
    if verbose:
        cmd.extend(["-v", "--tb=short"])
    else:
        cmd.extend(["-q"])
    
    if coverage:
        cmd.extend(["--cov=main", "--cov-report=term-missing"])
    
    # Ejecutar tests
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent, capture_output=True, text=True)
        
        print("=" * 60)
        print("SALIDA DE TESTS:")
        print("=" * 60)
        print(result.stdout)
        
        if result.stderr:
            print("=" * 60)
            print("ERRORES:")
            print("=" * 60)
            print(result.stderr)
        
        print("=" * 60)
        print(f"CÓDIGO DE SALIDA: {result.returncode}")
        print("=" * 60)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error ejecutando tests: {e}")
        return False

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Test Runner para Agentic RAG Service")
    parser.add_argument("--test-file", help="Archivo de test específico (ej: test_api.py)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Salida detallada")
    parser.add_argument("--coverage", "-c", action="store_true", help="Reporte de cobertura")
    parser.add_argument("--list", "-l", action="store_true", help="Listar archivos de test")
    
    args = parser.parse_args()
    
    # Cambiar al directorio del script
    os.chdir(Path(__file__).parent)
    
    if args.list:
        print("📋 Archivos de test disponibles:")
        test_dir = Path("tests")
        if test_dir.exists():
            for test_file in test_dir.glob("test_*.py"):
                print(f"  - {test_file.name}")
        else:
            print("  ❌ No se encontró el directorio tests/")
        return
    
    # Configurar entorno
    setup_test_environment()
    
    # Ejecutar tests
    print("🧪 Ejecutando tests...")
    success = run_tests(args.test_file, args.verbose, args.coverage)
    
    if success:
        print("✅ Todos los tests pasaron!")
        sys.exit(0)
    else:
        print("❌ Algunos tests fallaron")
        sys.exit(1)

if __name__ == "__main__":
    main() 