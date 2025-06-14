#!/usr/bin/env python3
"""
Test runner para el Sumiller Service
Ejecuta todos los tests con la configuración adecuada
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Ejecutar suite de tests"""
    print("🧪 SUMILLER SERVICE - TEST RUNNER")
    print("=" * 50)
    
    # Configurar entorno de tests
    os.environ["ENVIRONMENT"] = "test"
    os.environ["PYTHONPATH"] = str(Path.cwd())
    
    # Comandos de test
    test_commands = [
        # Tests unitarios (memoria)
        ["python3", "-m", "pytest", "tests/test_memory.py", "-v", "--tb=short"],
        
        # Tests de API
        ["python3", "-m", "pytest", "tests/test_api.py", "-v", "--tb=short"],
        
        # Tests de producción (smoke tests)
        ["python3", "-m", "pytest", "tests/test_production.py", "-v", "--tb=short"],
    ]
    
    total_failed = 0
    
    for i, cmd in enumerate(test_commands, 1):
        test_name = cmd[3].split('/')[-1]
        print(f"\n🔬 Ejecutando {test_name} ({i}/{len(test_commands)})...")
        print("-" * 40)
        
        try:
            result = subprocess.run(cmd, cwd=Path.cwd(), capture_output=False)
            if result.returncode != 0:
                total_failed += 1
                print(f"❌ {test_name} falló")
            else:
                print(f"✅ {test_name} completado")
        except Exception as e:
            print(f"❌ Error ejecutando {test_name}: {e}")
            total_failed += 1
    
    # Resumen final
    print("\n" + "=" * 50)
    if total_failed == 0:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
        return 0
    else:
        print(f"❌ {total_failed} suite(s) de tests fallaron")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 