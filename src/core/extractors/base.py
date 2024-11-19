from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from ...exceptions.classification import ExtractionError
import logging

logger = logging.getLogger(__name__)

@dataclass
class ExtractedContent:
    """Container for extracted document content."""
    text: str
    metadata: Dict[str, Any]
    tables: Optional[List[List[str]]] = None
    headers: Optional[List[str]] = None
    footers: Optional[List[str]] = None
    images: Optional[List[bytes]] = None
    page_count: Optional[int] = None
    language: Optional[str] = None
    confidence: Optional[float] = None

class BaseExtractor(ABC):
    """Base class for all format-specific extractors."""

    @property
    @abstractmethod
    def supported_mimes(self) -> List[str]:
        """List of MIME types this extractor can handle."""
        pass

    @abstractmethod
    def extract_content(self, file_path: str) -> ExtractedContent:
        """Extract content from the file."""
        pass

    @abstractmethod
    def validate_file(self, file_path: str) -> bool:
        """Validate if file is properly formatted."""
        pass

    def _clean_text(self, text: str) -> str:
        """Clean extracted text content."""
        if not text:
            return ""
        # Remove excessive whitespace
        text = " ".join(text.split())
        # Remove control characters
        text = "".join(char for char in text if ord(char) >= 32 or char in "\n\t")
        return text.strip()

    def _extract_tables(self, content: Any) -> List[List[str]]:
        """Extract tables from content. To be implemented by specific extractors."""
        return []

    def _detect_language(self, text: str) -> Optional[str]:
        """Detect language of text content."""
        try:
            from langdetect import detect
            return detect(text) if text else None
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}")
            return None

    def _calculate_confidence(self, text: str) -> float:
        """Calculate confidence score for extraction quality."""
        if not text:
            return 0.0
        # Simple heuristic based on text length and character validity
        valid_chars = sum(1 for c in text if c.isprintable())
        return min(1.0, valid_chars / len(text))
