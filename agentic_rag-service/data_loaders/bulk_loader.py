"""
Cargador masivo para procesar múltiples archivos
Coordina la carga de todos los tipos de datos
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .json_loader import JSONLoader
from .text_loader import TextLoader

logger = logging.getLogger(__name__)

class BulkLoader:
    """Cargador masivo para múltiples archivos"""
    
    def __init__(self):
        self.json_loader = JSONLoader()
        self.text_loader = TextLoader()
        self.supported_extensions = {
            '.json': self.json_loader.load_file,
            '.txt': self.text_loader.load_file,
            '.md': self.text_loader.load_file,
        }
        self.stats = {
            'files_processed': 0,
            'documents_loaded': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    async def load_directory(self, directory_path: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        Carga todos los archivos soportados de un directorio
        
        Args:
            directory_path: Ruta al directorio
            recursive: Si buscar en subdirectorios
            
        Returns:
            Lista de todos los documentos cargados
        """
        self.stats['start_time'] = datetime.now()
        logger.info(f"Iniciando carga masiva desde: {directory_path}")
        
        try:
            path = Path(directory_path)
            if not path.exists():
                logger.error(f"Directorio no encontrado: {directory_path}")
                return []
            
            # Encontrar archivos soportados
            files = self._find_supported_files(path, recursive)
            logger.info(f"Encontrados {len(files)} archivos para procesar")
            
            # Procesar archivos en paralelo (con límite)
            all_documents = []
            semaphore = asyncio.Semaphore(5)  # Máximo 5 archivos simultáneos
            
            tasks = [
                self._process_file_with_semaphore(semaphore, file_path)
                for file_path in files
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Consolidar resultados
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error en tarea: {result}")
                    self.stats['errors'] += 1
                elif isinstance(result, list):
                    all_documents.extend(result)
                    self.stats['documents_loaded'] += len(result)
            
            self.stats['end_time'] = datetime.now()
            self._log_stats()
            
            return all_documents
            
        except Exception as e:
            logger.error(f"Error en carga masiva: {e}")
            self.stats['errors'] += 1
            return []
    
    async def load_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Carga una lista específica de archivos
        
        Args:
            file_paths: Lista de rutas de archivos
            
        Returns:
            Lista de documentos cargados
        """
        self.stats['start_time'] = datetime.now()
        logger.info(f"Cargando {len(file_paths)} archivos específicos")
        
        all_documents = []
        semaphore = asyncio.Semaphore(5)
        
        tasks = [
            self._process_file_with_semaphore(semaphore, file_path)
            for file_path in file_paths
            if self._is_supported_file(Path(file_path))
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error procesando archivo: {result}")
                self.stats['errors'] += 1
            elif isinstance(result, list):
                all_documents.extend(result)
                self.stats['documents_loaded'] += len(result)
        
        self.stats['end_time'] = datetime.now()
        self._log_stats()
        
        return all_documents
    
    async def watch_directory(self, directory_path: str, callback=None) -> None:
        """
        Monitorea un directorio para cambios y carga archivos nuevos/modificados
        
        Args:
            directory_path: Directorio a monitorear
            callback: Función a llamar cuando se cargan nuevos documentos
        """
        logger.info(f"Iniciando monitoreo de directorio: {directory_path}")
        
        path = Path(directory_path)
        if not path.exists():
            logger.error(f"Directorio no encontrado: {directory_path}")
            return
        
        # Obtener estado inicial
        file_states = self._get_file_states(path)
        
        while True:
            try:
                await asyncio.sleep(10)  # Verificar cada 10 segundos
                
                current_states = self._get_file_states(path)
                changed_files = self._detect_changes(file_states, current_states)
                
                if changed_files:
                    logger.info(f"Detectados {len(changed_files)} archivos modificados")
                    documents = await self.load_files(changed_files)
                    
                    if callback and documents:
                        await callback(documents)
                
                file_states = current_states
                
            except Exception as e:
                logger.error(f"Error en monitoreo: {e}")
                await asyncio.sleep(30)  # Esperar más tiempo si hay error
    
    def _find_supported_files(self, path: Path, recursive: bool) -> List[str]:
        """Encuentra archivos soportados en el directorio"""
        files = []
        
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for file_path in path.glob(pattern):
            if file_path.is_file() and self._is_supported_file(file_path):
                files.append(str(file_path))
        
        return files
    
    def _is_supported_file(self, file_path: Path) -> bool:
        """Verifica si el archivo es soportado"""
        return file_path.suffix.lower() in self.supported_extensions
    
    async def _process_file_with_semaphore(self, semaphore: asyncio.Semaphore, file_path: str) -> List[Dict[str, Any]]:
        """Procesa un archivo con control de concurrencia"""
        async with semaphore:
            return await self._process_single_file(file_path)
    
    async def _process_single_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Procesa un archivo individual"""
        try:
            path = Path(file_path)
            extension = path.suffix.lower()
            
            if extension in self.supported_extensions:
                loader_func = self.supported_extensions[extension]
                documents = await loader_func(file_path)
                
                self.stats['files_processed'] += 1
                logger.debug(f"Procesado {file_path}: {len(documents)} documentos")
                
                return documents
            else:
                logger.warning(f"Extensión no soportada: {extension}")
                return []
                
        except Exception as e:
            logger.error(f"Error procesando {file_path}: {e}")
            self.stats['errors'] += 1
            return []
    
    def _get_file_states(self, path: Path) -> Dict[str, float]:
        """Obtiene timestamps de modificación de archivos"""
        states = {}
        
        for file_path in path.rglob("*"):
            if file_path.is_file() and self._is_supported_file(file_path):
                try:
                    states[str(file_path)] = file_path.stat().st_mtime
                except OSError:
                    continue
        
        return states
    
    def _detect_changes(self, old_states: Dict[str, float], new_states: Dict[str, float]) -> List[str]:
        """Detecta archivos nuevos o modificados"""
        changed = []
        
        # Archivos nuevos
        for file_path in new_states:
            if file_path not in old_states:
                changed.append(file_path)
                logger.debug(f"Archivo nuevo: {file_path}")
        
        # Archivos modificados
        for file_path, mtime in new_states.items():
            if file_path in old_states and old_states[file_path] != mtime:
                changed.append(file_path)
                logger.debug(f"Archivo modificado: {file_path}")
        
        return changed
    
    def _log_stats(self):
        """Registra estadísticas de la carga"""
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            
            logger.info(f"""
            === ESTADÍSTICAS DE CARGA MASIVA ===
            Archivos procesados: {self.stats['files_processed']}
            Documentos cargados: {self.stats['documents_loaded']}
            Errores: {self.stats['errors']}
            Duración: {duration.total_seconds():.2f} segundos
            Promedio: {self.stats['documents_loaded'] / max(1, self.stats['files_processed']):.1f} docs/archivo
            """)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de la última carga"""
        stats = self.stats.copy()
        
        if stats['start_time'] and stats['end_time']:
            stats['duration_seconds'] = (stats['end_time'] - stats['start_time']).total_seconds()
            stats['docs_per_file'] = stats['documents_loaded'] / max(1, stats['files_processed'])
        
        return stats
    
    def reset_stats(self):
        """Reinicia las estadísticas"""
        self.stats = {
            'files_processed': 0,
            'documents_loaded': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        } 