"""
Cargador especializado para archivos JSON
Procesa vinos, bodegas, regiones y otros datos estructurados
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class JSONLoader:
    """Cargador especializado para archivos JSON"""
    
    def __init__(self):
        self.supported_types = {
            'vinos': self._process_wine_data,
            'bodegas': self._process_winery_data,
            'regiones': self._process_region_data,
            'maridajes': self._process_pairing_data
        }
    
    async def load_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Carga un archivo JSON y lo procesa según su tipo
        
        Args:
            file_path: Ruta al archivo JSON
            
        Returns:
            Lista de documentos procesados
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"Archivo no encontrado: {file_path}")
                return []
            
            # Leer archivo JSON
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Determinar tipo de datos
            file_type = self._detect_file_type(path.name, data)
            logger.info(f"Procesando archivo {file_path} como tipo: {file_type}")
            
            # Procesar según tipo
            if file_type in self.supported_types:
                documents = await self.supported_types[file_type](data, path.name)
            else:
                documents = await self._process_generic_data(data, path.name)
            
            logger.info(f"Cargados {len(documents)} documentos desde {file_path}")
            return documents
            
        except json.JSONDecodeError as e:
            logger.error(f"Error JSON en {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error cargando {file_path}: {e}")
            return []
    
    def _detect_file_type(self, filename: str, data: Any) -> str:
        """Detecta el tipo de archivo basado en nombre y contenido"""
        
        # Detección por nombre de archivo
        filename_lower = filename.lower()
        for file_type in self.supported_types.keys():
            if file_type in filename_lower:
                return file_type
        
        # Detección por estructura de datos
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            if isinstance(first_item, dict):
                # Detectar vinos por campos característicos
                wine_fields = {'name', 'type', 'grape', 'vintage', 'price'}
                if wine_fields.issubset(set(first_item.keys())):
                    return 'vinos'
                
                # Detectar bodegas
                winery_fields = {'name', 'region', 'founded', 'wines'}
                if winery_fields.issubset(set(first_item.keys())):
                    return 'bodegas'
                
                # Detectar regiones
                region_fields = {'name', 'country', 'climate', 'grapes'}
                if region_fields.issubset(set(first_item.keys())):
                    return 'regiones'
        
        return 'generic'
    
    async def _process_wine_data(self, data: List[Dict], filename: str) -> List[Dict[str, Any]]:
        """Procesa datos de vinos"""
        documents = []
        
        for wine in data:
            try:
                # Crear documento principal del vino
                doc = {
                    'content': self._create_wine_description(wine),
                    'metadata': {
                        'type': 'vino',
                        'source': filename,
                        'wine_name': wine.get('name', ''),
                        'wine_type': wine.get('type', ''),
                        'region': wine.get('region', ''),
                        'grape': wine.get('grape', ''),
                        'vintage': wine.get('vintage', ''),
                        'price': wine.get('price', 0),
                        'rating': wine.get('rating', 0),
                        'alcohol': wine.get('alcohol', 0),
                        'winery': wine.get('winery', ''),
                        'loaded_at': datetime.now().isoformat()
                    }
                }
                documents.append(doc)
                
                # Crear documento de maridaje si existe
                if wine.get('pairing'):
                    pairing_doc = {
                        'content': f"Maridajes para {wine['name']}: {wine['pairing']}",
                        'metadata': {
                            'type': 'maridaje',
                            'source': filename,
                            'wine_name': wine.get('name', ''),
                            'wine_type': wine.get('type', ''),
                            'loaded_at': datetime.now().isoformat()
                        }
                    }
                    documents.append(pairing_doc)
                
            except Exception as e:
                logger.error(f"Error procesando vino {wine.get('name', 'unknown')}: {e}")
                continue
        
        return documents
    
    async def _process_winery_data(self, data: List[Dict], filename: str) -> List[Dict[str, Any]]:
        """Procesa datos de bodegas"""
        documents = []
        
        for winery in data:
            try:
                doc = {
                    'content': self._create_winery_description(winery),
                    'metadata': {
                        'type': 'bodega',
                        'source': filename,
                        'winery_name': winery.get('name', ''),
                        'region': winery.get('region', ''),
                        'founded': winery.get('founded', ''),
                        'loaded_at': datetime.now().isoformat()
                    }
                }
                documents.append(doc)
                
            except Exception as e:
                logger.error(f"Error procesando bodega {winery.get('name', 'unknown')}: {e}")
                continue
        
        return documents
    
    async def _process_region_data(self, data: List[Dict], filename: str) -> List[Dict[str, Any]]:
        """Procesa datos de regiones vitivinícolas"""
        documents = []
        
        for region in data:
            try:
                doc = {
                    'content': self._create_region_description(region),
                    'metadata': {
                        'type': 'region',
                        'source': filename,
                        'region_name': region.get('name', ''),
                        'country': region.get('country', ''),
                        'loaded_at': datetime.now().isoformat()
                    }
                }
                documents.append(doc)
                
            except Exception as e:
                logger.error(f"Error procesando región {region.get('name', 'unknown')}: {e}")
                continue
        
        return documents
    
    async def _process_pairing_data(self, data: List[Dict], filename: str) -> List[Dict[str, Any]]:
        """Procesa datos de maridajes"""
        documents = []
        
        for pairing in data:
            try:
                doc = {
                    'content': self._create_pairing_description(pairing),
                    'metadata': {
                        'type': 'maridaje',
                        'source': filename,
                        'food_type': pairing.get('food_type', ''),
                        'wine_type': pairing.get('wine_type', ''),
                        'loaded_at': datetime.now().isoformat()
                    }
                }
                documents.append(doc)
                
            except Exception as e:
                logger.error(f"Error procesando maridaje: {e}")
                continue
        
        return documents
    
    async def _process_generic_data(self, data: Any, filename: str) -> List[Dict[str, Any]]:
        """Procesa datos genéricos JSON"""
        documents = []
        
        try:
            # Convertir a string para búsqueda
            content = json.dumps(data, ensure_ascii=False, indent=2)
            
            doc = {
                'content': content,
                'metadata': {
                    'type': 'json_generic',
                    'source': filename,
                    'loaded_at': datetime.now().isoformat()
                }
            }
            documents.append(doc)
            
        except Exception as e:
            logger.error(f"Error procesando datos genéricos: {e}")
        
        return documents
    
    def _create_wine_description(self, wine: Dict) -> str:
        """Crea descripción textual de un vino"""
        parts = []
        
        # Información básica
        parts.append(f"Vino: {wine.get('name', 'Sin nombre')}")
        parts.append(f"Tipo: {wine.get('type', 'No especificado')}")
        parts.append(f"Región: {wine.get('region', 'No especificada')}")
        parts.append(f"Uva: {wine.get('grape', 'No especificada')}")
        
        # Detalles técnicos
        if wine.get('vintage'):
            parts.append(f"Añada: {wine['vintage']}")
        if wine.get('alcohol'):
            parts.append(f"Graduación: {wine['alcohol']}%")
        if wine.get('temperature'):
            parts.append(f"Temperatura de servicio: {wine['temperature']}")
        
        # Información comercial
        if wine.get('price'):
            parts.append(f"Precio: {wine['price']}€")
        if wine.get('rating'):
            parts.append(f"Puntuación: {wine['rating']}/100")
        if wine.get('stock'):
            parts.append(f"Stock: {wine['stock']} unidades")
        
        # Descripción y bodega
        if wine.get('description'):
            parts.append(f"Descripción: {wine['description']}")
        if wine.get('winery'):
            parts.append(f"Bodega: {wine['winery']}")
        if wine.get('pairing'):
            parts.append(f"Maridajes: {wine['pairing']}")
        
        return "\n".join(parts)
    
    def _create_winery_description(self, winery: Dict) -> str:
        """Crea descripción textual de una bodega"""
        parts = []
        
        parts.append(f"Bodega: {winery.get('name', 'Sin nombre')}")
        parts.append(f"Región: {winery.get('region', 'No especificada')}")
        
        if winery.get('founded'):
            parts.append(f"Fundada: {winery['founded']}")
        if winery.get('description'):
            parts.append(f"Descripción: {winery['description']}")
        if winery.get('wines'):
            wines_list = ", ".join(winery['wines']) if isinstance(winery['wines'], list) else str(winery['wines'])
            parts.append(f"Vinos: {wines_list}")
        
        return "\n".join(parts)
    
    def _create_region_description(self, region: Dict) -> str:
        """Crea descripción textual de una región"""
        parts = []
        
        parts.append(f"Región: {region.get('name', 'Sin nombre')}")
        parts.append(f"País: {region.get('country', 'No especificado')}")
        
        if region.get('climate'):
            parts.append(f"Clima: {region['climate']}")
        if region.get('grapes'):
            grapes_list = ", ".join(region['grapes']) if isinstance(region['grapes'], list) else str(region['grapes'])
            parts.append(f"Uvas principales: {grapes_list}")
        if region.get('description'):
            parts.append(f"Descripción: {region['description']}")
        
        return "\n".join(parts)
    
    def _create_pairing_description(self, pairing: Dict) -> str:
        """Crea descripción textual de un maridaje"""
        parts = []
        
        if pairing.get('food_type'):
            parts.append(f"Tipo de comida: {pairing['food_type']}")
        if pairing.get('wine_type'):
            parts.append(f"Tipo de vino: {pairing['wine_type']}")
        if pairing.get('description'):
            parts.append(f"Descripción: {pairing['description']}")
        if pairing.get('examples'):
            examples = ", ".join(pairing['examples']) if isinstance(pairing['examples'], list) else str(pairing['examples'])
            parts.append(f"Ejemplos: {examples}")
        
        return "\n".join(parts) 