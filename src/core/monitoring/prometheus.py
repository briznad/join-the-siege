from prometheus_client import Counter, Histogram, Gauge, Summary
from typing import Dict

# Document Processing Metrics
PROCESSING_TIME = Histogram(
    'document_processing_seconds',
    'Time spent processing documents',
    ['industry', 'document_type']
)

PROCESSED_DOCUMENTS = Counter(
    'documents_processed_total',
    'Number of documents processed',
    ['industry', 'status', 'document_type']
)

PROCESSING_ERRORS = Counter(
    'document_processing_errors_total',
    'Number of processing errors',
    ['error_type', 'industry']
)

# Queue Metrics
QUEUE_SIZE = Gauge(
    'document_queue_size',
    'Number of documents in processing queue',
    ['queue_name']
)

BATCH_SIZE = Histogram(
    'batch_size',
    'Distribution of batch sizes',
    buckets=[1, 5, 10, 20, 50, 100, 200, 500]
)

# Worker Metrics
WORKER_STATUS = Gauge(
    'worker_status',
    'Worker health status',
    ['worker_id']
)

WORKER_PROCESSING_TIME = Summary(
    'worker_processing_time_seconds',
    'Time spent processing by workers',
    ['worker_id']
)

# Extraction Metrics
EXTRACTION_TIME = Histogram(
    'extraction_time_seconds',
    'Time spent extracting content',
    ['extractor_type']
)

EXTRACTION_ERRORS = Counter(
    'extraction_errors_total',
    'Number of content extraction errors',
    ['extractor_type', 'error_type']
)

# Classification Metrics
CLASSIFICATION_CONFIDENCE = Histogram(
    'classification_confidence',
    'Distribution of classification confidence scores',
    ['industry', 'document_type'],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

MISCLASSIFICATION_RATE = Gauge(
    'misclassification_rate',
    'Rate of document misclassifications',
    ['industry']
)

# System Metrics
SYSTEM_MEMORY_USAGE = Gauge(
    'system_memory_bytes',
    'System memory usage in bytes',
    ['type']
)

SYSTEM_CPU_USAGE = Gauge(
    'system_cpu_percent',
    'System CPU usage percentage',
)

# Cache Metrics
CACHE_HITS = Counter(
    'cache_hits_total',
    'Number of cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Number of cache misses',
    ['cache_type']
)
