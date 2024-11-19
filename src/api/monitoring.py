from flask import Blueprint, jsonify, Response, current_app
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from ..core.monitoring.prometheus import (
    PROCESSING_TIME, PROCESSED_DOCUMENTS, 
    PROCESSING_ERRORS, QUEUE_SIZE, WORKER_STATUS
)
from ..core.storage import DocumentStore
from ..utils.logging import MetricsLogger
import logging
import psutil
import time

monitoring = Blueprint('monitoring', __name__)
logger = logging.getLogger(__name__)
metrics_logger = MetricsLogger()

@monitoring.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@monitoring.route('/health')
def health():
    try:
        workers_healthy = all(
            status.value > 0 
            for status in WORKER_STATUS.collect()[0].samples
        )
        
        total_docs = sum(m.value for m in PROCESSED_DOCUMENTS.collect()[0].samples)
        total_errors = sum(m.value for m in PROCESSING_ERRORS.collect()[0].samples)
        error_rate = (total_errors / total_docs) if total_docs > 0 else 0
        
        queue_sizes = {
            sample.labels['queue_name']: sample.value
            for sample in QUEUE_SIZE.collect()[0].samples
        }
        
        system_metrics = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }
        
        system_healthy = (
            workers_healthy and 
            error_rate < 0.1 and
            system_metrics['cpu_percent'] < 90 and
            system_metrics['memory_percent'] < 90 and
            system_metrics['disk_usage'] < 90
        )
        
        health_status = {
            "status": "healthy" if system_healthy else "degraded",
            "workers": {
                "healthy": workers_healthy,
                "count": len(list(WORKER_STATUS.collect()[0].samples))
            },
            "queues": queue_sizes,
            "metrics": {
                "error_rate": error_rate,
                "total_documents_processed": total_docs,
                "total_errors": total_errors,
                "average_processing_time": PROCESSING_TIME.describe()[0].sum / total_docs if total_docs > 0 else 0
            },
            "system": system_metrics,
            "timestamp": int(time.time())
        }
        
        return jsonify(health_status), 200 if system_healthy else 503

    except Exception as e:
        logger.error(f"Error checking health: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@monitoring.route('/stats')
def statistics():
    try:
        store = DocumentStore()
        
        doc_types = {}
        for sample in PROCESSED_DOCUMENTS.collect()[0].samples:
            doc_type = sample.labels.get('document_type', 'unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + sample.value
        
        error_types = {}
        for sample in PROCESSING_ERRORS.collect()[0].samples:
            error_type = sample.labels.get('error_type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + sample.value

        process = psutil.Process()
        memory_info = process.memory_info()
        
        stats = {
            "document_types": doc_types,
            "error_types": error_types,
            "processing_times": {
                "p50": PROCESSING_TIME.describe()[0].quantiles[0.50],
                "p95": PROCESSING_TIME.describe()[0].quantiles[0.95],
                "p99": PROCESSING_TIME.describe()[0].quantiles[0.99]
            },
            "system": {
                "cpu_percent": process.cpu_percent(),
                "memory": {
                    "rss": memory_info.rss,
                    "vms": memory_info.vms,
                    "percent": process.memory_percent()
                },
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections())
            }
        }
        
        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@monitoring.route('/stats/performance')
def performance_stats():
    try:
        current_time = time.time()
        window = int(current_app.config.get('STATS_WINDOW_SECONDS', 3600))
        start_time = current_time - window
        
        metrics = metrics_logger.get_metrics(start_time)
        
        throughput = len(metrics) / window if window > 0 else 0
        
        if metrics:
            processing_times = [m['processing_time_ms'] for m in metrics]
            avg_processing_time = sum(processing_times) / len(processing_times)
            max_processing_time = max(processing_times)
        else:
            avg_processing_time = 0
            max_processing_time = 0
        
        return jsonify({
            "window_seconds": window,
            "documents_processed": len(metrics),
            "throughput_per_second": throughput,
            "processing_times": {
                "average_ms": avg_processing_time,
                "maximum_ms": max_processing_time
            }
        }), 200

    except Exception as e:
        logger.error(f"Error getting performance stats: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@monitoring.route('/stats/errors')
def error_stats():
    try:
        current_time = time.time()
        window = int(current_app.config.get('STATS_WINDOW_SECONDS', 3600))
        start_time = current_time - window
        
        errors = metrics_logger.get_errors(start_time)
        
        error_counts = {}
        for error in errors:
            error_type = error.get('error_type', 'unknown')
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return jsonify({
            "window_seconds": window,
            "total_errors": len(errors),
            "error_types": error_counts
        }), 200

    except Exception as e:
        logger.error(f"Error getting error stats: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@monitoring.route('/debug/queues')
def debug_queues():
    try:
        queue_stats = {}
        for sample in QUEUE_SIZE.collect()[0].samples:
            queue_name = sample.labels['queue_name']
            queue_stats[queue_name] = {
                "size": sample.value,
                "rate": PROCESSED_DOCUMENTS.labels(queue=queue_name)._value.get()
            }
        
        return jsonify(queue_stats), 200

    except Exception as e:
        logger.error(f"Error getting queue debug info: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
