from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class BaseIndustryStrategy(ABC):
    """Base strategy for industry-specific document classification."""
    
    @property
    @abstractmethod
    def industry_name(self) -> str:
        """Return the name of the industry this strategy handles."""
        pass

    @property
    @abstractmethod
    def document_types(self) -> List[str]:
        """Return list of document types this strategy can classify."""
        pass

    @property
    @abstractmethod
    def keywords(self) -> Dict[str, List[str]]:
        """Return keyword mappings for document classification."""
        pass

    @abstractmethod
    def custom_rules(self, text: str, metadata: dict) -> Optional[str]:
        """Apply industry-specific classification rules."""
        pass

    def classify(self, text: str, metadata: Optional[dict] = None) -> Dict[str, Any]:
        """
        Classify document using industry-specific rules and keywords.
        
        Args:
            text: Extracted text content from document
            metadata: Additional document metadata
            
        Returns:
            Dictionary containing classification results
        """
        try:
            metadata = metadata or {}
            
            # Try custom rules first
            doc_type = self.custom_rules(text, metadata)
            if doc_type:
                return {
                    'document_type': doc_type,
                    'confidence_score': 0.9,  # High confidence for custom rules
                    'method': 'custom_rules'
                }

            # Fall back to keyword matching
            best_match = None
            best_score = 0
            
            text = text.lower()
            for doc_type, keywords in self.keywords.items():
                score = self._calculate_keyword_score(text, keywords)
                if score > best_score:
                    best_score = score
                    best_match = doc_type

            return {
                'document_type': best_match or 'unknown',
                'confidence_score': best_score,
                'method': 'keyword_matching'
            }

        except Exception as e:
            logger.error(f"Classification error in {self.industry_name} strategy: {str(e)}")
            return {
                'document_type': 'unknown',
                'confidence_score': 0.0,
                'method': 'error',
                'error': str(e)
            }

    def _calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """Calculate confidence score based on keyword matches."""
        if not keywords:
            return 0.0
        
        matches = sum(1 for keyword in keywords if keyword.lower() in text)
        return matches / len(keywords)

    def validate_document_type(self, document_type: str) -> bool:
        """Validate if document type is supported by this strategy."""
        return document_type in self.document_types

    @classmethod
    def get_strategy_metadata(cls) -> Dict[str, Any]:
        """Get metadata about the strategy."""
        instance = cls()
        return {
            'industry': instance.industry_name,
            'supported_types': instance.document_types,
            'keyword_count': sum(len(keywords) for keywords in instance.keywords.values())
        }
