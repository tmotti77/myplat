"""Document ingestion service with OCR, parsing, and PII scrubbing."""
import asyncio
import hashlib
import mimetypes
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import aiofiles
import pandas as pd
from unstructured.partition.auto import partition
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.docx import partition_docx
from unstructured.partition.html import partition_html
from unstructured.cleaners.core import clean
import pytesseract
from PIL import Image
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from src.core.config import settings
from src.core.database import get_db_session
from src.core.logging import get_logger, LoggerMixin, LoggedOperation
from src.models.document import Document, DocumentStatus, DocumentType
from src.models.chunk import Chunk, ChunkType
from src.models.source import Source
from src.services.cache import cache_service
from src.services.embedding import embedding_service
from src.services.storage import storage_service
from src.services.vector_store import vector_store_service

logger = get_logger(__name__)


class IngestionService(LoggerMixin):
    """Service for ingesting and processing documents."""
    
    def __init__(self):
        self._pii_analyzer = None
        self._pii_anonymizer = None
        self._supported_formats = {
            'application/pdf': DocumentType.PDF,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': DocumentType.DOCX,
            'application/msword': DocumentType.DOC,
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': DocumentType.PPTX,
            'application/vnd.ms-powerpoint': DocumentType.PPT,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': DocumentType.XLSX,
            'application/vnd.ms-excel': DocumentType.XLS,
            'text/plain': DocumentType.TXT,
            'text/markdown': DocumentType.MD,
            'text/html': DocumentType.HTML,
            'application/xml': DocumentType.XML,
            'application/json': DocumentType.JSON,
            'text/csv': DocumentType.CSV,
            'application/rtf': DocumentType.RTF,
            'image/jpeg': DocumentType.IMAGE,
            'image/png': DocumentType.IMAGE,
            'image/tiff': DocumentType.IMAGE,
        }
    
    async def initialize(self):
        """Initialize ingestion service."""
        try:
            # Initialize PII detection engines
            self._pii_analyzer = AnalyzerEngine()
            self._pii_anonymizer = AnonymizerEngine()
            
            self.log_info("Ingestion service initialized")
            
        except Exception as e:
            self.log_error("Failed to initialize ingestion service", error=e)
            raise
    
    async def cleanup(self):
        """Clean up ingestion service."""
        try:
            self.log_info("Ingestion service cleaned up")
        except Exception as e:
            self.log_error("Error during ingestion cleanup", error=e)
    
    async def ingest_document(
        self,
        file_data: Union[bytes, str],  # File content or path
        filename: str,
        tenant_id: str,
        source_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        processing_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Ingest and process a document."""
        
        document_id = str(uuid.uuid4())
        
        with LoggedOperation("document_ingestion", document_id=document_id, filename=filename):
            try:
                # Determine content type and validate
                content_type = self._detect_content_type(filename, file_data)
                if not self._is_supported_format(content_type):
                    raise ValueError(f"Unsupported file format: {content_type}")
                
                # Create document record
                document = await self._create_document_record(
                    document_id=document_id,
                    filename=filename,
                    content_type=content_type,
                    tenant_id=tenant_id,
                    source_id=source_id,
                    metadata=metadata or {}
                )
                
                # Upload to storage
                storage_info = await storage_service.upload_file(
                    file_data=file_data,
                    tenant_id=tenant_id,
                    document_id=document_id,
                    filename=filename,
                    content_type=content_type,
                    metadata=metadata
                )
                
                # Update document with storage info
                await self._update_document_storage_info(document, storage_info)
                
                # Schedule async processing
                asyncio.create_task(
                    self._process_document_async(
                        document_id=document_id,
                        storage_info=storage_info,
                        processing_config=processing_config or {}
                    )
                )
                
                return {
                    "document_id": document_id,
                    "status": DocumentStatus.PROCESSING.value,
                    "storage_info": storage_info,
                    "content_type": content_type,
                    "estimated_processing_time": self._estimate_processing_time(
                        content_type, storage_info.get("file_size", 0)
                    )
                }
                
            except Exception as e:
                # Mark document as failed if it was created
                if 'document' in locals():
                    await self._mark_document_failed(document, str(e))
                
                self.log_error(
                    "Document ingestion failed",
                    document_id=document_id,
                    filename=filename,
                    error=e
                )
                raise
    
    async def _process_document_async(
        self,
        document_id: str,
        storage_info: Dict[str, Any],
        processing_config: Dict[str, Any]
    ):
        """Process document asynchronously."""
        
        try:
            async with get_db_session() as session:
                # Get document
                document = await session.get(Document, document_id)
                if not document:
                    self.log_error("Document not found for processing", document_id=document_id)
                    return
                
                # Mark as processing
                document.status = DocumentStatus.PROCESSING.value
                document.processing_started_at = datetime.utcnow().isoformat() + "Z"
                await session.commit()
            
            # Download file from storage
            file_content = await storage_service.download_file(storage_info["object_key"])
            
            # Extract text and metadata
            extraction_result = await self._extract_text_and_metadata(
                file_content=file_content,
                content_type=document.content_type,
                processing_config=processing_config
            )
            
            # PII detection and scrubbing
            pii_result = await self._detect_and_scrub_pii(
                extraction_result["text"],
                processing_config.get("scrub_pii", True)
            )
            
            # Update document with extracted content
            await self._update_document_content(
                document_id=document_id,
                extraction_result=extraction_result,
                pii_result=pii_result
            )
            
            # Create chunks
            chunks = await self._create_chunks(
                document_id=document_id,
                text=pii_result["cleaned_text"],
                extraction_result=extraction_result,
                processing_config=processing_config
            )
            
            # Generate embeddings for chunks
            await self._generate_chunk_embeddings(
                chunks=chunks,
                tenant_id=document.tenant_id,
                embedding_model=processing_config.get(
                    "embedding_model", 
                    settings.EMBEDDING_MODEL
                )
            )
            
            # Index in vector store
            await self._index_chunks_in_vector_store(
                chunks=chunks,
                tenant_id=document.tenant_id,
                embedding_model=processing_config.get(
                    "embedding_model",
                    settings.EMBEDDING_MODEL
                )
            )
            
            # Mark document as processed
            await self._mark_document_processed(document_id, len(chunks))
            
            self.log_info(
                "Document processing completed",
                document_id=document_id,
                chunks_created=len(chunks)
            )
            
        except Exception as e:
            await self._mark_document_failed(document_id, str(e))
            self.log_error(
                "Document processing failed",
                document_id=document_id,
                error=e
            )
    
    async def _extract_text_and_metadata(
        self,
        file_content: bytes,
        content_type: str,
        processing_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract text and metadata from file content."""
        
        try:
            # Save to temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name
            
            try:
                # Extract based on content type
                if content_type == "application/pdf":
                    elements = await self._extract_from_pdf(
                        temp_path, processing_config
                    )
                elif content_type in [
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "application/msword"
                ]:
                    elements = await self._extract_from_docx(
                        temp_path, processing_config
                    )
                elif content_type in ["text/html"]:
                    elements = await self._extract_from_html(
                        temp_path, processing_config
                    )
                elif content_type.startswith("image/"):
                    elements = await self._extract_from_image(
                        temp_path, processing_config
                    )
                else:
                    # Generic text extraction
                    elements = await self._extract_generic(
                        temp_path, processing_config
                    )
                
                # Process elements
                result = await self._process_extracted_elements(elements)
                
                return result
                
            finally:
                # Clean up temp file
                try:
                    Path(temp_path).unlink()
                except:
                    pass
                    
        except Exception as e:
            self.log_error("Text extraction failed", content_type=content_type, error=e)
            # Return minimal result
            return {
                "text": "",
                "word_count": 0,
                "page_count": 0,
                "has_images": False,
                "has_tables": False,
                "has_links": False,
                "structure": [],
                "metadata": {}
            }
    
    async def _extract_from_pdf(
        self,
        file_path: str,
        processing_config: Dict[str, Any]
    ) -> List[Any]:
        """Extract content from PDF file."""
        
        try:
            # Use unstructured library for PDF parsing
            elements = await asyncio.get_event_loop().run_in_executor(
                None,
                partition_pdf,
                file_path,
                # Configuration options
                True,  # extract_images
                processing_config.get("extract_images", True),
                processing_config.get("extract_tables", True),
                processing_config.get("ocr_enabled", True)
            )
            
            return elements
            
        except Exception as e:
            self.log_error("PDF extraction failed", file_path=file_path, error=e)
            raise
    
    async def _extract_from_docx(
        self,
        file_path: str,
        processing_config: Dict[str, Any]
    ) -> List[Any]:
        """Extract content from DOCX file."""
        
        try:
            elements = await asyncio.get_event_loop().run_in_executor(
                None,
                partition_docx,
                file_path
            )
            
            return elements
            
        except Exception as e:
            self.log_error("DOCX extraction failed", file_path=file_path, error=e)
            raise
    
    async def _extract_from_html(
        self,
        file_path: str,
        processing_config: Dict[str, Any]
    ) -> List[Any]:
        """Extract content from HTML file."""
        
        try:
            elements = await asyncio.get_event_loop().run_in_executor(
                None,
                partition_html,
                file_path
            )
            
            return elements
            
        except Exception as e:
            self.log_error("HTML extraction failed", file_path=file_path, error=e)
            raise
    
    async def _extract_from_image(
        self,
        file_path: str,
        processing_config: Dict[str, Any]
    ) -> List[Any]:
        """Extract text from image using OCR."""
        
        try:
            if not processing_config.get("ocr_enabled", True):
                return []
            
            # Use Tesseract OCR
            text = await asyncio.get_event_loop().run_in_executor(
                None,
                self._ocr_image,
                file_path,
                processing_config.get("languages", ["eng"])
            )
            
            # Create mock element structure
            if text.strip():
                return [{
                    "type": "text",
                    "text": text,
                    "metadata": {"source": "ocr"}
                }]
            
            return []
            
        except Exception as e:
            self.log_error("Image OCR failed", file_path=file_path, error=e)
            return []
    
    def _ocr_image(self, file_path: str, languages: List[str]) -> str:
        """Perform OCR on image file."""
        
        try:
            # Open image
            image = Image.open(file_path)
            
            # Configure Tesseract
            lang_config = "+".join(languages)
            config = "--oem 3 --psm 6"  # Use LSTM OCR and uniform text block
            
            # Extract text
            text = pytesseract.image_to_string(
                image,
                lang=lang_config,
                config=config
            )
            
            return text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return ""
    
    async def _extract_generic(
        self,
        file_path: str,
        processing_config: Dict[str, Any]
    ) -> List[Any]:
        """Generic text extraction for various formats."""
        
        try:
            elements = await asyncio.get_event_loop().run_in_executor(
                None,
                partition,
                file_path
            )
            
            return elements
            
        except Exception as e:
            self.log_error("Generic extraction failed", file_path=file_path, error=e)
            # Fallback to reading as text
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                return [{
                    "type": "text",
                    "text": text,
                    "metadata": {}
                }]
            except:
                return []
    
    async def _process_extracted_elements(self, elements: List[Any]) -> Dict[str, Any]:
        """Process extracted elements into structured format."""
        
        text_parts = []
        structure = []
        has_images = False
        has_tables = False
        has_links = False
        page_count = 0
        
        for element in elements:
            if hasattr(element, 'text') and element.text:
                # Clean text
                cleaned_text = clean(element.text, extra_whitespace=True)
                text_parts.append(cleaned_text)
                
                # Determine element type
                element_type = getattr(element, 'type', 'text')
                if hasattr(element, 'category'):
                    element_type = element.category
                
                structure.append({
                    "type": element_type,
                    "text": cleaned_text[:200],  # First 200 chars for structure
                    "length": len(cleaned_text)
                })
                
                # Check for special content
                if element_type in ["Image", "FigureCaption"]:
                    has_images = True
                elif element_type in ["Table"]:
                    has_tables = True
                elif "http" in cleaned_text.lower():
                    has_links = True
            
            # Track page information
            if hasattr(element, 'metadata') and element.metadata:
                page_num = element.metadata.get('page_number', 0)
                page_count = max(page_count, page_num)
        
        # Combine all text
        full_text = "\n\n".join(text_parts)
        word_count = len(full_text.split())
        
        return {
            "text": full_text,
            "word_count": word_count,
            "page_count": max(1, page_count),
            "has_images": has_images,
            "has_tables": has_tables,
            "has_links": has_links,
            "structure": structure,
            "metadata": {
                "extraction_method": "unstructured",
                "elements_count": len(elements)
            }
        }
    
    async def _detect_and_scrub_pii(
        self,
        text: str,
        scrub_enabled: bool = True
    ) -> Dict[str, Any]:
        """Detect and optionally scrub PII from text."""
        
        try:
            if not text.strip():
                return {
                    "cleaned_text": text,
                    "pii_detected": False,
                    "pii_categories": [],
                    "pii_entities": []
                }
            
            # Analyze for PII
            analyzer_results = await asyncio.get_event_loop().run_in_executor(
                None,
                self._pii_analyzer.analyze,
                text,
                "en"  # Language
            )
            
            # Extract PII information
            pii_categories = list(set([result.entity_type for result in analyzer_results]))
            pii_entities = [
                {
                    "type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "confidence": result.score,
                    "text": text[result.start:result.end]
                }
                for result in analyzer_results
            ]
            
            # Scrub PII if enabled
            cleaned_text = text
            if scrub_enabled and analyzer_results:
                anonymized_result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._pii_anonymizer.anonymize,
                    text,
                    analyzer_results
                )
                cleaned_text = anonymized_result.text
            
            return {
                "cleaned_text": cleaned_text,
                "pii_detected": len(analyzer_results) > 0,
                "pii_categories": pii_categories,
                "pii_entities": pii_entities
            }
            
        except Exception as e:
            self.log_error("PII detection/scrubbing failed", error=e)
            # Return original text on failure
            return {
                "cleaned_text": text,
                "pii_detected": False,
                "pii_categories": [],
                "pii_entities": []
            }
    
    async def _create_chunks(
        self,
        document_id: str,
        text: str,
        extraction_result: Dict[str, Any],
        processing_config: Dict[str, Any]
    ) -> List[Chunk]:
        """Create text chunks from document content."""
        
        try:
            if not text.strip():
                return []
            
            # Get chunking configuration
            chunk_size = processing_config.get("chunk_size", settings.CHUNK_SIZE)
            chunk_overlap = processing_config.get("chunk_overlap", settings.CHUNK_OVERLAP)
            
            # Split text into chunks
            chunks = await self._split_text_into_chunks(
                text=text,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                structure=extraction_result.get("structure", [])
            )
            
            # Create chunk objects
            chunk_objects = []
            
            async with get_db_session() as session:
                for idx, chunk_data in enumerate(chunks):
                    chunk = Chunk(
                        id=str(uuid.uuid4()),
                        document_id=document_id,
                        idx=idx,
                        text=chunk_data["text"],
                        text_clean=self._clean_text_for_search(chunk_data["text"]),
                        chunk_type=chunk_data.get("type", ChunkType.TEXT.value),
                        section=chunk_data.get("section", ""),
                        page_number=chunk_data.get("page_number"),
                        tokens=len(chunk_data["text"].split()),
                        characters=len(chunk_data["text"]),
                        words=len(chunk_data["text"].split()),
                        sentences=chunk_data["text"].count('.') + chunk_data["text"].count('!') + chunk_data["text"].count('?'),
                        language=processing_config.get("language", "en"),
                        quality_score=self._calculate_chunk_quality(chunk_data["text"]),
                        embedding_model=processing_config.get("embedding_model", settings.EMBEDDING_MODEL),
                        processed_at=datetime.utcnow().isoformat() + "Z"
                    )
                    
                    session.add(chunk)
                    chunk_objects.append(chunk)
                
                await session.commit()
            
            return chunk_objects
            
        except Exception as e:
            self.log_error("Chunk creation failed", document_id=document_id, error=e)
            return []
    
    async def _split_text_into_chunks(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int,
        structure: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks with structure awareness."""
        
        chunks = []
        
        # Simple sentence-aware splitting
        sentences = self._split_into_sentences(text)
        
        current_chunk = ""
        current_tokens = 0
        current_section = ""
        
        for sentence in sentences:
            sentence_tokens = len(sentence.split())
            
            # Check if adding this sentence would exceed chunk size
            if current_tokens + sentence_tokens > chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    "text": current_chunk.strip(),
                    "tokens": current_tokens,
                    "section": current_section,
                    "type": ChunkType.TEXT.value
                })
                
                # Start new chunk with overlap
                if chunk_overlap > 0:
                    overlap_words = current_chunk.split()[-chunk_overlap:]
                    current_chunk = " ".join(overlap_words) + " "
                    current_tokens = len(overlap_words)
                else:
                    current_chunk = ""
                    current_tokens = 0
            
            # Add sentence to current chunk
            current_chunk += sentence + " "
            current_tokens += sentence_tokens
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "tokens": current_tokens,
                "section": current_section,
                "type": ChunkType.TEXT.value
            })
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        
        # Simple sentence splitting (could be improved with NLTK)
        import re
        
        # Split on sentence endings, but preserve abbreviations
        sentence_endings = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
        sentences = sentence_endings.split(text)
        
        return [s.strip() for s in sentences if s.strip()]
    
    def _clean_text_for_search(self, text: str) -> str:
        """Clean text for full-text search indexing."""
        
        import re
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that interfere with search
        text = re.sub(r'[^\w\s\-_.,!?;:]', ' ', text)
        
        return text.strip()
    
    def _calculate_chunk_quality(self, text: str) -> float:
        """Calculate quality score for chunk."""
        
        score = 0.5  # Base score
        
        # Length factor
        word_count = len(text.split())
        if 50 <= word_count <= 200:
            score += 0.2
        elif 20 <= word_count < 50 or 200 < word_count <= 400:
            score += 0.1
        
        # Complete sentences
        if text.strip().endswith(('.', '!', '?')):
            score += 0.1
        
        # Has uppercase (proper nouns, etc.)
        if any(c.isupper() for c in text):
            score += 0.1
        
        # Not too repetitive
        words = text.lower().split()
        unique_words = set(words)
        if len(words) > 0:
            uniqueness = len(unique_words) / len(words)
            score += uniqueness * 0.1
        
        return min(1.0, max(0.0, score))
    
    async def _generate_chunk_embeddings(
        self,
        chunks: List[Chunk],
        tenant_id: str,
        embedding_model: str
    ):
        """Generate embeddings for chunks."""
        
        try:
            if not chunks:
                return
            
            # Extract texts for embedding
            texts = [chunk.text for chunk in chunks]
            
            # Generate embeddings in batches
            embeddings = await embedding_service.generate_embeddings(
                texts=texts,
                model=embedding_model,
                tenant_id=tenant_id,
                batch_size=32
            )
            
            # Save embeddings to database
            async with get_db_session() as session:
                for chunk, embedding in zip(chunks, embeddings):
                    from src.models.embedding import Embedding
                    
                    embedding_obj = Embedding(
                        chunk_id=chunk.id,
                        model=embedding_model,
                        dimensions=len(embedding),
                        vector=embedding,
                        generated_at=datetime.utcnow().isoformat() + "Z"
                    )
                    
                    session.add(embedding_obj)
                
                await session.commit()
            
            self.log_info(
                "Chunk embeddings generated",
                chunk_count=len(chunks),
                model=embedding_model
            )
            
        except Exception as e:
            self.log_error("Embedding generation failed", error=e)
            raise
    
    async def _index_chunks_in_vector_store(
        self,
        chunks: List[Chunk],
        tenant_id: str,
        embedding_model: str
    ):
        """Index chunks in vector store."""
        
        try:
            if not chunks:
                return
            
            # Prepare vector data
            vectors = []
            
            async with get_db_session() as session:
                for chunk in chunks:
                    # Get embedding
                    from src.models.embedding import Embedding
                    from sqlalchemy import select
                    
                    query = select(Embedding).where(
                        Embedding.chunk_id == chunk.id,
                        Embedding.model == embedding_model
                    )
                    result = await session.execute(query)
                    embedding = result.scalar_one_or_none()
                    
                    if embedding and embedding.vector:
                        vectors.append({
                            "id": str(chunk.id),
                            "vector": embedding.get_vector_array(),
                            "payload": {
                                "tenant_id": tenant_id,
                                "document_id": str(chunk.document_id),
                                "chunk_type": chunk.chunk_type,
                                "language": chunk.language,
                                "quality_score": chunk.quality_score,
                                "tokens": chunk.tokens,
                                "section": chunk.section or "",
                                "page_number": chunk.page_number or 0
                            }
                        })
            
            if vectors:
                # Ensure collection exists
                vector_size = len(vectors[0]["vector"]) if vectors else 1536
                await vector_store_service.create_collection(
                    tenant_id=tenant_id,
                    embedding_model=embedding_model,
                    vector_size=vector_size
                )
                
                # Upsert vectors
                await vector_store_service.upsert_vectors(
                    tenant_id=tenant_id,
                    embedding_model=embedding_model,
                    vectors=vectors
                )
                
                self.log_info(
                    "Chunks indexed in vector store",
                    chunk_count=len(vectors),
                    tenant_id=tenant_id
                )
            
        except Exception as e:
            self.log_error("Vector store indexing failed", error=e)
            # Don't raise - this is not critical for document processing
    
    def _detect_content_type(self, filename: str, file_data: Union[bytes, str]) -> str:
        """Detect content type from filename and content."""
        
        # Try to detect from filename
        content_type, _ = mimetypes.guess_type(filename)
        
        if content_type:
            return content_type
        
        # Fallback detection from content (if bytes)
        if isinstance(file_data, bytes):
            # Check for PDF magic number
            if file_data.startswith(b'%PDF'):
                return 'application/pdf'
            
            # Check for ZIP-based formats (DOCX, XLSX, etc.)
            if file_data.startswith(b'PK'):
                if b'word/' in file_data[:2048]:
                    return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                elif b'xl/' in file_data[:2048]:
                    return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                elif b'ppt/' in file_data[:2048]:
                    return 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            
            # Check for image formats
            if file_data.startswith(b'\xff\xd8\xff'):
                return 'image/jpeg'
            elif file_data.startswith(b'\x89PNG'):
                return 'image/png'
        
        # Default to plain text
        return 'text/plain'
    
    def _is_supported_format(self, content_type: str) -> bool:
        """Check if content type is supported."""
        return content_type in self._supported_formats
    
    def _estimate_processing_time(self, content_type: str, file_size: int) -> int:
        """Estimate processing time in seconds."""
        
        # Base time estimates (in seconds)
        base_times = {
            'application/pdf': 30,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 15,
            'text/plain': 5,
            'text/html': 10,
            'image/jpeg': 45,  # OCR takes time
            'image/png': 45,
        }
        
        base_time = base_times.get(content_type, 20)
        
        # Adjust for file size (per MB)
        size_mb = file_size / (1024 * 1024)
        size_factor = max(1, size_mb * 0.5)
        
        return int(base_time * size_factor)
    
    async def _create_document_record(
        self,
        document_id: str,
        filename: str,
        content_type: str,
        tenant_id: str,
        source_id: str,
        metadata: Dict[str, Any]
    ) -> Document:
        """Create document record in database."""
        
        async with get_db_session() as session:
            document = Document(
                id=document_id,
                tenant_id=tenant_id,
                source_id=source_id,
                title=filename,
                content_type=self._supported_formats.get(content_type, DocumentType.OTHER).value,
                mime_type=content_type,
                status=DocumentStatus.PENDING.value,
                version=1,
                language=metadata.get("language", "en"),
                metadata=metadata
            )
            
            session.add(document)
            await session.commit()
            
            return document
    
    async def _update_document_storage_info(
        self,
        document: Document,
        storage_info: Dict[str, Any]
    ):
        """Update document with storage information."""
        
        async with get_db_session() as session:
            # Merge document into session
            document = await session.merge(document)
            
            document.file_path = storage_info["object_key"]
            document.size_bytes = storage_info["file_size"]
            document.hash_sha256 = storage_info["file_hash"]
            
            await session.commit()
    
    async def _update_document_content(
        self,
        document_id: str,
        extraction_result: Dict[str, Any],
        pii_result: Dict[str, Any]
    ):
        """Update document with extracted content."""
        
        async with get_db_session() as session:
            document = await session.get(Document, document_id)
            
            if document:
                document.text_content = extraction_result["text"]
                document.word_count = extraction_result["word_count"]
                document.page_count = extraction_result["page_count"]
                document.has_images = "true" if extraction_result["has_images"] else "false"
                document.has_tables = "true" if extraction_result["has_tables"] else "false"
                document.has_links = "true" if extraction_result["has_links"] else "false"
                document.contains_pii = "true" if pii_result["pii_detected"] else "false"
                document.pii_categories = pii_result["pii_categories"]
                
                await session.commit()
    
    async def _mark_document_processed(self, document_id: str, chunk_count: int):
        """Mark document as successfully processed."""
        
        async with get_db_session() as session:
            document = await session.get(Document, document_id)
            
            if document:
                document.mark_as_processed()
                document.chunk_count = chunk_count
                
                await session.commit()
    
    async def _mark_document_failed(self, document: Union[Document, str], error: str):
        """Mark document as failed."""
        
        async with get_db_session() as session:
            if isinstance(document, str):
                document = await session.get(Document, document)
            else:
                document = await session.merge(document)
            
            if document:
                document.mark_as_failed(error)
                await session.commit()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check ingestion service health."""
        
        health = {
            "status": "healthy",
            "pii_analyzer_available": self._pii_analyzer is not None,
            "supported_formats": len(self._supported_formats),
            "ocr_available": False,
        }
        
        # Check OCR availability
        try:
            pytesseract.get_tesseract_version()
            health["ocr_available"] = True
        except:
            pass
        
        return health


# Global ingestion service instance
ingestion_service = IngestionService()