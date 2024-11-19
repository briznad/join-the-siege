from typing import Dict, Type, Optional
from .base import BaseExtractor
import magic
import logging
from ...exceptions.classification import ExtractionError

logger = logging.getLogger(__name__)

class ExtractorRegistry:
    """Registry for file format extractors."""

    def __init__(self):
        self._extractors: Dict[str, Type[BaseExtractor]] = {}
        self._mime = magic.Magic(mime=True)

    def register(self, extractor_class: Type[BaseExtractor]):
        """Register an extractor for its supported MIME types."""
        extractor = extractor_class()
        for mime_type in extractor.supported_mimes:
            self._extractors[mime_type] = extractor_class
            logger.info(f"Registered extractor {extractor_class.__name__} for MIME type {mime_type}")

    def get_extractor(self, file_path: str) -> BaseExtractor:
        """Get appropriate extractor for a file."""
        try:
            mime_type = self._mime.from_file(file_path)
            extractor_class = self._extractors.get(mime_type)

            if not extractor_class:
                raise ExtractionError(f"No extractor registered for MIME type: {mime_type}")

            return extractor_class()
        except Exception as e:
            raise ExtractionError(f"Error determining file type: {str(e)}")

    def get_supported_mime_types(self) -> Dict[str, str]:
        """Get all supported MIME types and their corresponding extractors."""
        return {
            mime_type: extractor.__name__
            for mime_type, extractor in self._extractors.items()
        }

    def validate_mime_type(self, mime_type: str) -> bool:
        """Check if MIME type is supported."""
        return mime_type in self._extractors

    def get_extractor_for_mime_type(self, mime_type: str) -> Optional[BaseExtractor]:
        """Get extractor instance for specific MIME type."""
        extractor_class = self._extractors.get(mime_type)
        return extractor_class() if extractor_class else None
