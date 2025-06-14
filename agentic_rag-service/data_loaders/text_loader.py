"""
Cargador especializado para archivos de texto
Procesa documentos .txt y .md con extracción de metadatos
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TextLoader:
    """Cargador especializado para archivos de texto"""
    
    def __init__(self):
        self.chunk_size = 1000  # Tamaño de chunks en caracteres
        self.chunk_overlap = 200  # Solapamiento entre chunks
    
    async def load_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Carga un archivo de texto y lo procesa en chunks
        
        Args:
            file_path: Ruta al archivo de texto
            
        Returns:
            Lista de documentos procesados
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"Archivo no encontrado: {file_path}")
                return []
            
            # Leer contenido
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                logger.warning(f"Archivo vacío: {file_path}")
                return []
            
            # Extraer metadatos del contenido
            metadata = self._extract_metadata(content, path)
            
            # Dividir en chunks si es necesario
            if len(content) > self.chunk_size:
                documents = self._create_chunks(content, metadata, path.name)
            else:
                documents = [self._create_document(content, metadata, path.name)]
            
            logger.info(f"Cargados {len(documents)} documentos desde {file_path}")
            return documents
            
        except UnicodeDecodeError as e:
            logger.error(f"Error de codificación en {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error cargando {file_path}: {e}")
            return []
    
    def _extract_metadata(self, content: str, path: Path) -> Dict[str, Any]:
        """Extrae metadatos del contenido del archivo"""
        metadata = {
            'type': 'texto',
            'source': path.name,
            'file_extension': path.suffix,
            'loaded_at': datetime.now().isoformat()
        }
        
        # Detectar tipo de contenido por extensión
        if path.suffix.lower() == '.md':
            metadata['format'] = 'markdown'
            metadata.update(self._extract_markdown_metadata(content))
        else:
            metadata['format'] = 'text'
            metadata.update(self._extract_text_metadata(content))
        
        # Estadísticas básicas
        metadata.update({
            'word_count': len(content.split()),
            'char_count': len(content),
            'line_count': len(content.splitlines())
        })
        
        return metadata
    
    def _extract_markdown_metadata(self, content: str) -> Dict[str, Any]:
        """Extrae metadatos específicos de Markdown"""
        metadata = {}
        
        # Extraer título principal (primer H1)
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            metadata['title'] = h1_match.group(1).strip()
        
        # Contar headers
        headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
        metadata['header_count'] = len(headers)
        
        # Extraer enlaces
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        metadata['link_count'] = len(links)
        
        # Extraer bloques de código
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        metadata['code_block_count'] = len(code_blocks)
        
        # Detectar listas
        list_items = re.findall(r'^\s*[-*+]\s+', content, re.MULTILINE)
        metadata['list_item_count'] = len(list_items)
        
        return metadata
    
    def _extract_text_metadata(self, content: str) -> Dict[str, Any]:
        """Extrae metadatos de texto plano"""
        metadata = {}
        
        # Intentar extraer título (primera línea si parece título)
        lines = content.splitlines()
        if lines:
            first_line = lines[0].strip()
            if len(first_line) < 100 and not first_line.endswith('.'):
                metadata['title'] = first_line
        
        # Detectar estructura por patrones
        if re.search(r'^\s*#', content, re.MULTILINE):
            metadata['has_sections'] = True
        
        # Contar párrafos (líneas separadas por líneas vacías)
        paragraphs = re.split(r'\n\s*\n', content.strip())
        metadata['paragraph_count'] = len(paragraphs)
        
        # Detectar contenido especializado
        wine_keywords = ['vino', 'bodega', 'uva', 'crianza', 'maridaje', 'cata', 'sumiller']
        wine_matches = sum(1 for keyword in wine_keywords if keyword.lower() in content.lower())
        if wine_matches >= 3:
            metadata['content_type'] = 'vinos'
            metadata['wine_keyword_matches'] = wine_matches
        
        return metadata
    
    def _create_chunks(self, content: str, base_metadata: Dict[str, Any], filename: str) -> List[Dict[str, Any]]:
        """Divide el contenido en chunks manejables"""
        documents = []
        
        # Dividir por párrafos primero para mantener coherencia
        paragraphs = re.split(r'\n\s*\n', content.strip())
        
        current_chunk = ""
        chunk_number = 1
        
        for paragraph in paragraphs:
            # Si agregar este párrafo excede el tamaño, crear chunk actual
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                doc = self._create_chunk_document(
                    current_chunk.strip(), 
                    base_metadata, 
                    filename, 
                    chunk_number,
                    len(documents) + 1
                )
                documents.append(doc)
                
                # Iniciar nuevo chunk con solapamiento
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + paragraph
                chunk_number += 1
            else:
                # Agregar párrafo al chunk actual
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Agregar último chunk si tiene contenido
        if current_chunk.strip():
            doc = self._create_chunk_document(
                current_chunk.strip(), 
                base_metadata, 
                filename, 
                chunk_number,
                len(documents) + 1
            )
            documents.append(doc)
        
        return documents
    
    def _get_overlap_text(self, text: str) -> str:
        """Obtiene texto de solapamiento del final del chunk"""
        if len(text) <= self.chunk_overlap:
            return text
        
        # Buscar un punto de corte natural (final de oración)
        overlap_start = len(text) - self.chunk_overlap
        sentences = re.split(r'[.!?]+\s+', text[overlap_start:])
        
        if len(sentences) > 1:
            # Tomar desde la segunda oración para evitar cortes abruptos
            return sentences[1] + " "
        else:
            # Si no hay oraciones completas, tomar los últimos caracteres
            return text[-self.chunk_overlap:] + " "
    
    def _create_document(self, content: str, metadata: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Crea un documento simple sin chunks"""
        return {
            'content': content,
            'metadata': {
                **metadata,
                'is_chunked': False
            }
        }
    
    def _create_chunk_document(self, content: str, base_metadata: Dict[str, Any], filename: str, chunk_number: int, total_chunks: int) -> Dict[str, Any]:
        """Crea un documento chunk"""
        chunk_metadata = base_metadata.copy()
        chunk_metadata.update({
            'is_chunked': True,
            'chunk_number': chunk_number,
            'total_chunks': total_chunks,
            'chunk_id': f"{filename}_chunk_{chunk_number}"
        })
        
        return {
            'content': content,
            'metadata': chunk_metadata
        }
    
    def set_chunk_size(self, size: int, overlap: int = None):
        """Configura el tamaño de chunks"""
        self.chunk_size = size
        if overlap is not None:
            self.chunk_overlap = overlap
        
        logger.info(f"Configurado chunk_size={self.chunk_size}, overlap={self.chunk_overlap}")
    
    async def load_multiple_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Carga múltiples archivos de texto"""
        all_documents = []
        
        for file_path in file_paths:
            documents = await self.load_file(file_path)
            all_documents.extend(documents)
        
        return all_documents
    
    def get_supported_extensions(self) -> List[str]:
        """Retorna extensiones soportadas"""
        return ['.txt', '.md'] 