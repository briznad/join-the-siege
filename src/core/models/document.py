from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List

@dataclass
class Document:
    """Represents a classified document with metadata."""
    file_path: str
    document_type: str
    confidence_score: float
    mime_type: str
    file_size: int
    file_hash: str
    industry: Optional[str] = None
    extracted_text: Optional[str] = None
    metadata: Dict[str, Any] = None
    tables: List[List[str]] = None
    headers: List[str] = None
    footers: List[str] = None
    processed_at: datetime = None

    def __post_init__(self):
        if self.processed_at is None:
            self.processed_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict:
        """Convert document to dictionary representation."""
        return {
            'file_path': self.file_path,
            'document_type': self.document_type,
            'confidence_score': self.confidence_score,
            'mime_type': self.mime_type,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'industry': self.industry,
            'metadata': self.metadata,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Document':
        """Create document instance from dictionary."""
        if 'processed_at' in data and isinstance(data['processed_at'], str):
            data['processed_at'] = datetime.fromisoformat(data['processed_at'])
        return cls(**data)
