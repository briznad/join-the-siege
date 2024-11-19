from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
import time

@dataclass
class ProcessingMetrics:
    document_id: str
    start_time: datetime
    document_type: str
    industry: Optional[str] = None
    end_time: Optional[datetime] = None
    processing_time_ms: Optional[float] = None
    error: Optional[str] = None
    retries: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def complete(self, error: Optional[str] = None):
        self.end_time = datetime.utcnow()
        self.processing_time_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.error = error

@dataclass
class ExtractionMetrics:
    document_id: str
    extractor_type: str
    start_time: datetime
    content_size: int
    end_time: Optional[datetime] = None
    extraction_time_ms: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def complete(self, error: Optional[str] = None):
        self.end_time = datetime.utcnow()
        self.extraction_time_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.error = error

class MetricsAggregator:
    def __init__(self):
        self.processing_metrics: Dict[str, ProcessingMetrics] = {}
        self.extraction_metrics: Dict[str, ExtractionMetrics] = {}

    def start_processing(
        self,
        document_id: str,
        document_type: str,
        industry: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProcessingMetrics:
        metrics = ProcessingMetrics(
            document_id=document_id,
            start_time=datetime.utcnow(),
            document_type=document_type,
            industry=industry,
            metadata=metadata or {}
        )
        self.processing_metrics[document_id] = metrics
        return metrics

    def complete_processing(
        self,
        document_id: str,
        error: Optional[str] = None
    ) -> Optional[ProcessingMetrics]:
        if document_id in self.processing_metrics:
            metrics = self.processing_metrics[document_id]
            metrics.complete(error)
            return metrics
        return None

    def start_extraction(
        self,
        document_id: str,
        extractor_type: str,
        content_size: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExtractionMetrics:
        metrics = ExtractionMetrics(
            document_id=document_id,
            extractor_type=extractor_type,
            start_time=datetime.utcnow(),
            content_size=content_size,
            metadata=metadata or {}
        )
        self.extraction_metrics[document_id] = metrics
        return metrics

    def complete_extraction(
        self,
        document_id: str,
        error: Optional[str] = None
    ) -> Optional[ExtractionMetrics]:
        if document_id in self.extraction_metrics:
            metrics = self.extraction_metrics[document_id]
            metrics.complete(error)
            return metrics
        return None

    def get_processing_stats(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        metrics = [
            m for m in self.processing_metrics.values()
            if m.end_time and
            (not start_time or m.start_time >= start_time) and
            (not end_time or m.end_time <= end_time)
        ]

        if not metrics:
            return {
                "total_documents": 0,
                "average_processing_time": 0,
                "success_rate": 0,
                "error_rate": 0
            }

        successful = [m for m in metrics if not m.error]
        
        return {
            "total_documents": len(metrics),
            "average_processing_time": sum(m.processing_time_ms for m in metrics) / len(metrics),
            "success_rate": len(successful) / len(metrics),
            "error_rate": (len(metrics) - len(successful)) / len(metrics)
        }

    def get_extraction_stats(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Dict[str, Any]]:
        metrics = [
            m for m in self.extraction_metrics.values()
            if m.end_time and
            (not start_time or m.start_time >= start_time) and
            (not end_time or m.end_time <= end_time)
        ]

        stats_by_type = {}
        for extractor_type in set(m.extractor_type for m in metrics):
            type_metrics = [m for m in metrics if m.extractor_type == extractor_type]
            successful = [m for m in type_metrics if not m.error]
            
            stats_by_type[extractor_type] = {
                "total_extractions": len(type_metrics),
                "average_extraction_time": sum(m.extraction_time_ms for m in type_metrics) / len(type_metrics) if type_metrics else 0,
                "success_rate": len(successful) / len(type_metrics) if type_metrics else 0,
                "average_content_size": sum(m.content_size for m in type_metrics) / len(type_metrics) if type_metrics else 0
            }

        return stats_by_type
