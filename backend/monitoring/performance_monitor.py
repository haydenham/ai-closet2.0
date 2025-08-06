"""
Performance monitoring and metrics collection for Fashion AI Platform
"""
import time
import psutil
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from functools import wraps
import asyncio
from contextlib import contextmanager

from google.cloud import monitoring_v3
from google.cloud import logging as cloud_logging
import redis

from app.core.config import settings


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    labels: Dict[str, str]
    resource_type: str = "global"


@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_io_mb: float
    active_connections: int
    timestamp: datetime


class PerformanceMonitor:
    """Comprehensive performance monitoring system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics_buffer: List[PerformanceMetric] = []
        self.system_metrics_history: List[SystemMetrics] = []
        
        # Initialize Google Cloud Monitoring
        if settings.google_cloud_project:
            try:
                self.monitoring_client = monitoring_v3.MetricServiceClient()
                self.project_name = f"projects/{settings.google_cloud_project}"
                self.cloud_logging_client = cloud_logging.Client()
                self.cloud_logging_client.setup_logging()
            except Exception as e:
                self.logger.warning(f"Failed to initialize Cloud Monitoring: {e}")
                self.monitoring_client = None
        else:
            self.monitoring_client = None
        
        # Initialize Redis for metrics caching
        try:
            self.redis_client = redis.Redis.from_url(settings.redis_url)
        except Exception as e:
            self.logger.warning(f"Failed to initialize Redis: {e}")
            self.redis_client = None
    
    def record_metric(
        self, 
        name: str, 
        value: float, 
        unit: str = "1",
        labels: Optional[Dict[str, str]] = None
    ):
        """Record a custom metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.utcnow(),
            labels=labels or {},
            resource_type="global"
        )
        
        self.metrics_buffer.append(metric)
        
        # Send to Cloud Monitoring if available
        if self.monitoring_client:
            self._send_to_cloud_monitoring(metric)
        
        # Cache in Redis if available
        if self.redis_client:
            self._cache_metric(metric)
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system resource metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / 1024 / 1024
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # Network metrics
            network = psutil.net_io_counters()
            network_io_mb = (network.bytes_sent + network.bytes_recv) / 1024 / 1024
            
            # Connection metrics (approximate)
            connections = len(psutil.net_connections())
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                disk_usage_percent=disk_usage_percent,
                network_io_mb=network_io_mb,
                active_connections=connections,
                timestamp=datetime.utcnow()
            )
            
            self.system_metrics_history.append(metrics)
            
            # Keep only last 1000 entries
            if len(self.system_metrics_history) > 1000:
                self.system_metrics_history = self.system_metrics_history[-1000:]
            
            # Record as metrics
            self.record_metric("system.cpu_percent", cpu_percent, "%")
            self.record_metric("system.memory_percent", memory_percent, "%")
            self.record_metric("system.memory_used_mb", memory_used_mb, "MB")
            self.record_metric("system.disk_usage_percent", disk_usage_percent, "%")
            self.record_metric("system.active_connections", connections, "1")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            return SystemMetrics(0, 0, 0, 0, 0, 0, datetime.utcnow())
    
    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter recent metrics
        recent_metrics = [
            m for m in self.system_metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": "No metrics available for the specified time period"}
        
        # Calculate statistics
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        
        summary = {
            "time_period_hours": hours,
            "total_samples": len(recent_metrics),
            "cpu_stats": {
                "avg": sum(cpu_values) / len(cpu_values),
                "min": min(cpu_values),
                "max": max(cpu_values),
                "current": cpu_values[-1] if cpu_values else 0
            },
            "memory_stats": {
                "avg": sum(memory_values) / len(memory_values),
                "min": min(memory_values),
                "max": max(memory_values),
                "current": memory_values[-1] if memory_values else 0
            },
            "latest_metrics": asdict(recent_metrics[-1]) if recent_metrics else None
        }
        
        return summary
    
    def check_performance_thresholds(self) -> List[Dict[str, Any]]:
        """Check if any performance thresholds are exceeded"""
        alerts = []
        
        if not self.system_metrics_history:
            return alerts
        
        latest = self.system_metrics_history[-1]
        
        # Define thresholds
        thresholds = {
            "cpu_percent": {"warning": 70, "critical": 90},
            "memory_percent": {"warning": 80, "critical": 95},
            "disk_usage_percent": {"warning": 80, "critical": 95},
            "active_connections": {"warning": 100, "critical": 200}
        }
        
        for metric_name, levels in thresholds.items():
            value = getattr(latest, metric_name)
            
            if value >= levels["critical"]:
                alerts.append({
                    "severity": "critical",
                    "metric": metric_name,
                    "value": value,
                    "threshold": levels["critical"],
                    "timestamp": latest.timestamp
                })
            elif value >= levels["warning"]:
                alerts.append({
                    "severity": "warning",
                    "metric": metric_name,
                    "value": value,
                    "threshold": levels["warning"],
                    "timestamp": latest.timestamp
                })
        
        return alerts
    
    def _send_to_cloud_monitoring(self, metric: PerformanceMetric):
        """Send metric to Google Cloud Monitoring"""
        if not self.monitoring_client:
            return
        
        try:
            # Create time series data
            series = monitoring_v3.TimeSeries()
            series.metric.type = f"custom.googleapis.com/{metric.name}"
            
            # Add labels
            for key, value in metric.labels.items():
                series.metric.labels[key] = value
            
            # Set resource
            series.resource.type = metric.resource_type
            
            # Add data point
            point = monitoring_v3.Point()
            point.value.double_value = metric.value
            point.interval.end_time.seconds = int(metric.timestamp.timestamp())
            series.points = [point]
            
            # Send to Cloud Monitoring
            self.monitoring_client.create_time_series(
                name=self.project_name,
                time_series=[series]
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send metric to Cloud Monitoring: {e}")
    
    def _cache_metric(self, metric: PerformanceMetric):
        """Cache metric in Redis for fast retrieval"""
        if not self.redis_client:
            return
        
        try:
            key = f"metrics:{metric.name}:{int(metric.timestamp.timestamp())}"
            data = asdict(metric)
            
            # Store with 24-hour expiration
            self.redis_client.setex(
                key, 
                86400,  # 24 hours
                str(data)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to cache metric in Redis: {e}")
    
    def flush_metrics(self):
        """Flush buffered metrics"""
        if self.metrics_buffer:
            self.logger.info(f"Flushing {len(self.metrics_buffer)} metrics")
            self.metrics_buffer.clear()


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            try:
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                
                # Record metrics
                execution_time = end_time - start_time
                memory_used = end_memory - start_memory
                
                metric_labels = labels or {}
                metric_labels.update({
                    "function": func.__name__,
                    "success": str(success)
                })
                
                performance_monitor.record_metric(
                    f"{metric_name}.execution_time",
                    execution_time,
                    "s",
                    metric_labels
                )
                
                performance_monitor.record_metric(
                    f"{metric_name}.memory_used",
                    memory_used,
                    "MB",
                    metric_labels
                )
                
                if error:
                    metric_labels["error"] = error[:100]  # Truncate long errors
                    performance_monitor.record_metric(
                        f"{metric_name}.errors",
                        1,
                        "1",
                        metric_labels
                    )
            
            return result
        return wrapper
    return decorator


@contextmanager
def performance_context(operation_name: str, labels: Optional[Dict[str, str]] = None):
    """Context manager for monitoring code blocks"""
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    try:
        yield
        success = True
        error = None
    except Exception as e:
        success = False
        error = str(e)
        raise
    finally:
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        execution_time = end_time - start_time
        memory_used = end_memory - start_memory
        
        metric_labels = labels or {}
        metric_labels.update({
            "operation": operation_name,
            "success": str(success)
        })
        
        performance_monitor.record_metric(
            f"operation.{operation_name}.execution_time",
            execution_time,
            "s",
            metric_labels
        )
        
        performance_monitor.record_metric(
            f"operation.{operation_name}.memory_used",
            memory_used,
            "MB",
            metric_labels
        )
        
        if error:
            metric_labels["error"] = error[:100]
            performance_monitor.record_metric(
                f"operation.{operation_name}.errors",
                1,
                "1",
                metric_labels
            )


class DatabasePerformanceMonitor:
    """Specialized monitoring for database operations"""
    
    def __init__(self):
        self.query_stats = {}
        self.slow_queries = []
    
    def record_query(self, query: str, execution_time: float, rows_affected: int = 0):
        """Record database query performance"""
        # Normalize query for grouping
        normalized_query = self._normalize_query(query)
        
        if normalized_query not in self.query_stats:
            self.query_stats[normalized_query] = {
                "count": 0,
                "total_time": 0,
                "min_time": float('inf'),
                "max_time": 0,
                "total_rows": 0
            }
        
        stats = self.query_stats[normalized_query]
        stats["count"] += 1
        stats["total_time"] += execution_time
        stats["min_time"] = min(stats["min_time"], execution_time)
        stats["max_time"] = max(stats["max_time"], execution_time)
        stats["total_rows"] += rows_affected
        
        # Record slow queries
        if execution_time > 1.0:  # Queries taking more than 1 second
            self.slow_queries.append({
                "query": query[:200],  # Truncate long queries
                "execution_time": execution_time,
                "rows_affected": rows_affected,
                "timestamp": datetime.utcnow()
            })
            
            # Keep only last 100 slow queries
            if len(self.slow_queries) > 100:
                self.slow_queries = self.slow_queries[-100:]
        
        # Record metrics
        performance_monitor.record_metric(
            "database.query_time",
            execution_time,
            "s",
            {"query_type": self._get_query_type(query)}
        )
        
        performance_monitor.record_metric(
            "database.rows_affected",
            rows_affected,
            "1",
            {"query_type": self._get_query_type(query)}
        )
    
    def get_query_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive query performance report"""
        if not self.query_stats:
            return {"message": "No query statistics available"}
        
        # Calculate averages and sort by total time
        report_data = []
        for query, stats in self.query_stats.items():
            avg_time = stats["total_time"] / stats["count"]
            avg_rows = stats["total_rows"] / stats["count"]
            
            report_data.append({
                "query": query,
                "count": stats["count"],
                "total_time": stats["total_time"],
                "avg_time": avg_time,
                "min_time": stats["min_time"],
                "max_time": stats["max_time"],
                "avg_rows": avg_rows,
                "total_rows": stats["total_rows"]
            })
        
        # Sort by total time (most expensive queries first)
        report_data.sort(key=lambda x: x["total_time"], reverse=True)
        
        return {
            "total_queries": sum(stats["count"] for stats in self.query_stats.values()),
            "unique_queries": len(self.query_stats),
            "slow_queries_count": len(self.slow_queries),
            "top_queries": report_data[:10],  # Top 10 most expensive
            "recent_slow_queries": self.slow_queries[-10:]  # Last 10 slow queries
        }
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for grouping similar queries"""
        import re
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', query.strip())
        
        # Replace parameter placeholders
        normalized = re.sub(r'\$\d+', '?', normalized)
        normalized = re.sub(r"'[^']*'", "'?'", normalized)
        normalized = re.sub(r'\b\d+\b', '?', normalized)
        
        return normalized[:200]  # Truncate for storage efficiency
    
    def _get_query_type(self, query: str) -> str:
        """Determine query type from SQL"""
        query_lower = query.lower().strip()
        
        if query_lower.startswith('select'):
            return 'SELECT'
        elif query_lower.startswith('insert'):
            return 'INSERT'
        elif query_lower.startswith('update'):
            return 'UPDATE'
        elif query_lower.startswith('delete'):
            return 'DELETE'
        else:
            return 'OTHER'


# Global database performance monitor
db_performance_monitor = DatabasePerformanceMonitor()


# Async performance monitoring
class AsyncPerformanceMonitor:
    """Async performance monitoring for async operations"""
    
    @staticmethod
    async def monitor_async_operation(
        operation_name: str,
        coro,
        labels: Optional[Dict[str, str]] = None
    ):
        """Monitor async operation performance"""
        start_time = time.time()
        
        try:
            result = await coro
            success = True
            error = None
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            
            metric_labels = labels or {}
            metric_labels.update({
                "operation": operation_name,
                "success": str(success)
            })
            
            performance_monitor.record_metric(
                f"async.{operation_name}.execution_time",
                execution_time,
                "s",
                metric_labels
            )
            
            if error:
                metric_labels["error"] = error[:100]
                performance_monitor.record_metric(
                    f"async.{operation_name}.errors",
                    1,
                    "1",
                    metric_labels
                )
        
        return result


# Background task for continuous monitoring
async def continuous_monitoring_task():
    """Background task that continuously collects system metrics"""
    while True:
        try:
            # Collect system metrics
            performance_monitor.collect_system_metrics()
            
            # Check for alerts
            alerts = performance_monitor.check_performance_thresholds()
            if alerts:
                for alert in alerts:
                    performance_monitor.logger.warning(
                        f"Performance alert: {alert['severity']} - "
                        f"{alert['metric']} = {alert['value']} "
                        f"(threshold: {alert['threshold']})"
                    )
            
            # Flush metrics buffer periodically
            if len(performance_monitor.metrics_buffer) > 100:
                performance_monitor.flush_metrics()
            
            # Wait before next collection
            await asyncio.sleep(60)  # Collect every minute
            
        except Exception as e:
            performance_monitor.logger.error(f"Error in monitoring task: {e}")
            await asyncio.sleep(60)  # Continue monitoring even if there's an error