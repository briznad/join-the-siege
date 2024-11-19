import redis
from typing import Optional, Dict, List, Any
import json
import logging
from datetime import datetime
from .config import get_settings

logger = logging.getLogger(__name__)

class DocumentStore:
    """Storage handler for document metadata and processing status."""
    
    def __init__(self):
        settings = get_settings()
        self.redis = redis.Redis.from_url(settings.REDIS_URL)
        self.ttl = 86400  # 24 hours default TTL
    
    def store_document(self, doc_id: str, document: Dict[str, Any]) -> bool:
        """
        Store document metadata and content.
        
        Args:
            doc_id: Unique document identifier
            document: Dictionary containing document data and metadata
        """
        try:
            # Add timestamp
            document['stored_at'] = datetime.utcnow().isoformat()
            
            # Store document
            self.redis.setex(
                f"doc:{doc_id}",
                self.ttl,
                json.dumps(document)
            )
            
            # If this is part of a batch, add to batch set
            if 'batch_id' in document:
                self.redis.sadd(f"batch:{document['batch_id']}", doc_id)
                self.redis.expire(f"batch:{document['batch_id']}", self.ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing document {doc_id}: {str(e)}")
            return False
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document if it exists."""
        try:
            doc = self.redis.get(f"doc:{doc_id}")
            return json.loads(doc) if doc else None
        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {str(e)}")
            return None
    
    def update_document_status(
        self,
        doc_id: str,
        status: str,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update document processing status.
        
        Args:
            doc_id: Document identifier
            status: New status ('pending', 'processing', 'completed', 'failed', 'cancelled')
            task_id: Optional Celery task ID
            metadata: Optional additional metadata
        """
        try:
            doc = self.get_document(doc_id)
            if not doc:
                return False
            
            doc['status'] = status
            doc['updated_at'] = datetime.utcnow().isoformat()
            
            if task_id:
                doc['task_id'] = task_id
            
            if metadata:
                doc['metadata'] = {**(doc.get('metadata', {})), **metadata}
            
            return self.store_document(doc_id, doc)
            
        except Exception as e:
            logger.error(f"Error updating document {doc_id} status: {str(e)}")
            return False
    
    def get_batch_documents(self, batch_id: str) -> List[Dict[str, Any]]:
        """Get all documents in a batch."""
        try:
            # Get document IDs in batch
            doc_ids = self.redis.smembers(f"batch:{batch_id}")
            
            # Get documents
            documents = []
            for doc_id in doc_ids:
                doc = self.get_document(doc_id.decode('utf-8'))
                if doc:
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving batch {batch_id}: {str(e)}")
            return []
    
    def update_batch_status(
        self,
        batch_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update status for all documents in a batch."""
        try:
            documents = self.get_batch_documents(batch_id)
            
            for doc in documents:
                if doc.get('status') != 'completed':  # Don't update completed docs
                    self.update_document_status(
                        doc['id'],
                        status,
                        metadata=metadata
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating batch {batch_id} status: {str(e)}")
            return False
    
    def cleanup_expired_documents(self, batch_id: Optional[str] = None) -> int:
        """
        Clean up expired documents and their metadata.
        
        Args:
            batch_id: Optional batch ID to clean up specific batch
        
        Returns:
            Number of documents cleaned up
        """
        try:
            pattern = f"doc:*" if not batch_id else f"doc:*{batch_id}*"
            cleaned = 0
            
            for key in self.redis.scan_iter(pattern):
                if not self.redis.ttl(key):  # Key has no TTL or is expired
                    self.redis.delete(key)
                    cleaned += 1
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning up documents: {str(e)}")
            return 0
    
    def get_document_history(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get document processing history."""
        try:
            history_key = f"history:{doc_id}"
            history = self.redis.lrange(history_key, 0, -1)
            
            return [json.loads(entry) for entry in history]
            
        except Exception as e:
            logger.error(f"Error retrieving history for {doc_id}: {str(e)}")
            return []
    
    def add_history_entry(
        self,
        doc_id: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add entry to document history."""
        try:
            entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'action': action,
                'metadata': metadata or {}
            }
            
            history_key = f"history:{doc_id}"
            self.redis.lpush(history_key, json.dumps(entry))
            self.redis.ltrim(history_key, 0, 99)  # Keep last 100 entries
            self.redis.expire(history_key, self.ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding history entry for {doc_id}: {str(e)}")
            return False
    
    def get_processing_stats(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get document processing statistics."""
        try:
            # Get all documents
            documents = []
            for key in self.redis.scan_iter("doc:*"):
                doc = self.get_document(key.decode('utf-8').split(':')[1])
                if doc:
                    stored_at = datetime.fromisoformat(doc.get('stored_at', ''))
                    
                    if start_time and stored_at < datetime.fromisoformat(start_time):
                        continue
                    if end_time and stored_at > datetime.fromisoformat(end_time):
                        continue
                        
                    documents.append(doc)
            
            # Calculate stats
            total = len(documents)
            if not total:
                return {
                    'total_documents': 0,
                    'status_counts': {},
                    'document_types': {},
                    'average_processing_time': 0
                }
            
            status_counts = {}
            document_types = {}
            processing_times = []
            
            for doc in documents:
                status = doc.get('status', 'unknown')
                doc_type = doc.get('document_type', 'unknown')
                
                status_counts[status] = status_counts.get(status, 0) + 1
                document_types[doc_type] = document_types.get(doc_type, 0) + 1
                
                if doc.get('processing_time'):
                    processing_times.append(doc['processing_time'])
            
            return {
                'total_documents': total,
                'status_counts': status_counts,
                'document_types': document_types,
                'average_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting processing stats: {str(e)}")
            return {
                'error': str(e)
            }
