#!/usr/bin/env python3
"""
Script para carga manual de datos
Permite cargar archivos o directorios específicos
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import List

# Agregar el directorio padre al path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

from data_loaders import JSONLoader, TextLoader, BulkLoader

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/load_data.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

class DataLoadManager:
    """Gestor de carga de datos desde CLI"""
    
    def __init__(self):
        self.json_loader = JSONLoader()
        self.text_loader = TextLoader()
        self.bulk_loader = BulkLoader()
    
    async def load_file(self, file_path: str, force: bool = False) -> bool:
        """Carga un archivo específico"""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"Archivo no encontrado: {file_path}")
                return False
            
            logger.info(f"Cargando archivo: {file_path}")
            
            # Determinar tipo de cargador
            extension = path.suffix.lower()
            if extension == '.json':
                documents = await self.json_loader.load_file(file_path)
            elif extension in ['.txt', '.md']:
                documents = await self.text_loader.load_file(file_path)
            else:
                logger.error(f"Extensión no soportada: {extension}")
                return False
            
            if documents:
                logger.info(f"✅ Cargados {len(documents)} documentos desde {file_path}")
                self._print_document_summary(documents)
                return True
            else:
                logger.warning(f"⚠️ No se cargaron documentos desde {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error cargando {file_path}: {e}")
            return False
    
    async def load_directory(self, directory_path: str, recursive: bool = True, force: bool = False) -> bool:
        """Carga todos los archivos de un directorio"""
        try:
            path = Path(directory_path)
            if not path.exists():
                logger.error(f"Directorio no encontrado: {directory_path}")
                return False
            
            logger.info(f"Cargando directorio: {directory_path} (recursivo: {recursive})")
            
            documents = await self.bulk_loader.load_directory(directory_path, recursive)
            
            if documents:
                stats = self.bulk_loader.get_stats()
                logger.info(f"✅ Carga completada:")
                logger.info(f"   - Archivos procesados: {stats['files_processed']}")
                logger.info(f"   - Documentos cargados: {stats['documents_loaded']}")
                logger.info(f"   - Errores: {stats['errors']}")
                logger.info(f"   - Duración: {stats.get('duration_seconds', 0):.2f}s")
                
                self._print_document_summary(documents[:10])  # Mostrar solo primeros 10
                return True
            else:
                logger.warning(f"⚠️ No se cargaron documentos desde {directory_path}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error cargando directorio {directory_path}: {e}")
            return False
    
    def _print_document_summary(self, documents: List[dict]):
        """Imprime resumen de documentos cargados"""
        if not documents:
            return
        
        print("\n📄 RESUMEN DE DOCUMENTOS CARGADOS:")
        print("=" * 50)
        
        # Agrupar por tipo
        types = {}
        for doc in documents:
            doc_type = doc.get('metadata', {}).get('type', 'unknown')
            types[doc_type] = types.get(doc_type, 0) + 1
        
        for doc_type, count in types.items():
            print(f"  {doc_type}: {count} documentos")
        
        print(f"\nTotal: {len(documents)} documentos")
        
        # Mostrar algunos ejemplos
        print("\n📋 EJEMPLOS:")
        for i, doc in enumerate(documents[:3]):
            metadata = doc.get('metadata', {})
            content_preview = doc.get('content', '')[:100] + "..." if len(doc.get('content', '')) > 100 else doc.get('content', '')
            
            print(f"\n  [{i+1}] Tipo: {metadata.get('type', 'unknown')}")
            print(f"      Fuente: {metadata.get('source', 'unknown')}")
            print(f"      Contenido: {content_preview}")

async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Carga manual de datos para el servicio RAG')
    
    # Argumentos mutuamente excluyentes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--file', '-f', help='Archivo específico a cargar')
    group.add_argument('--directory', '-d', help='Directorio a cargar')
    
    # Opciones adicionales
    parser.add_argument('--recursive', '-r', action='store_true', default=True,
                       help='Buscar archivos recursivamente en subdirectorios')
    parser.add_argument('--no-recursive', action='store_false', dest='recursive',
                       help='No buscar en subdirectorios')
    parser.add_argument('--force', action='store_true',
                       help='Forzar recarga de archivos existentes')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mostrar información detallada')
    
    args = parser.parse_args()
    
    # Configurar nivel de logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Crear directorio de logs si no existe
    Path('logs').mkdir(exist_ok=True)
    
    # Inicializar gestor
    manager = DataLoadManager()
    
    try:
        success = False
        
        if args.file:
            success = await manager.load_file(args.file, args.force)
        elif args.directory:
            success = await manager.load_directory(args.directory, args.recursive, args.force)
        
        if success:
            print("\n🎉 Carga completada exitosamente!")
            sys.exit(0)
        else:
            print("\n❌ La carga falló o no se procesaron archivos")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Carga interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        print(f"\n💥 Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 