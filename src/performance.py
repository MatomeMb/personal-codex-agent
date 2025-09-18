"""
Performance Monitoring and Optimization for Personal Codex Agent

This module provides performance monitoring, caching, and optimization utilities.
"""

import time
import functools
import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict, deque
import threading
import json
from pathlib import Path

@dataclass
class PerformanceMetric:
    """Represents a single performance measurement"""
    function_name: str
    execution_time: float
    timestamp: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PerformanceMonitor:
    """Monitors and tracks performance metrics across the application"""
    
    def __init__(self, max_metrics: int = 1000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        
        # Performance statistics
        self.stats = defaultdict(list)
        self.error_count = 0
        self.total_calls = 0
        
    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        with self._lock:
            self.metrics.append(metric)
            self.stats[metric.function_name].append(metric.execution_time)
            self.total_calls += 1
            
            if not metric.success:
                self.error_count += 1
                
            # Log slow operations
            if metric.execution_time > 5.0:  # 5 seconds threshold
                self.logger.warning(f"Slow operation detected: {metric.function_name} took {metric.execution_time:.2f}s")
    
    def get_stats(self, function_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics for a function or all functions"""
        with self._lock:
            if function_name:
                if function_name not in self.stats:
                    return {}
                
                times = self.stats[function_name]
                return {
                    'function_name': function_name,
                    'call_count': len(times),
                    'avg_time': sum(times) / len(times) if times else 0,
                    'min_time': min(times) if times else 0,
                    'max_time': max(times) if times else 0,
                    'total_time': sum(times)
                }
            else:
                # Return stats for all functions
                all_stats = {}
                for func_name, times in self.stats.items():
                    all_stats[func_name] = {
                        'call_count': len(times),
                        'avg_time': sum(times) / len(times) if times else 0,
                        'min_time': min(times) if times else 0,
                        'max_time': max(times) if times else 0,
                        'total_time': sum(times)
                    }
                return all_stats
    
    def get_recent_metrics(self, limit: int = 100) -> List[PerformanceMetric]:
        """Get recent performance metrics"""
        with self._lock:
            return list(self.metrics)[-limit:]
    
    def get_error_rate(self) -> float:
        """Get overall error rate"""
        with self._lock:
            return self.error_count / self.total_calls if self.total_calls > 0 else 0.0
    
    def clear_metrics(self):
        """Clear all stored metrics"""
        with self._lock:
            self.metrics.clear()
            self.stats.clear()
            self.error_count = 0
            self.total_calls = 0

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def monitor_performance(func: Callable) -> Callable:
    """
    Decorator to monitor function performance
    
    Args:
        func: Function to monitor
        
    Returns:
        Wrapped function with performance monitoring
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        success = True
        error_message = None
        metadata = {}
        
        try:
            # Add some metadata about the call
            metadata['args_count'] = len(args)
            metadata['kwargs_count'] = len(kwargs)
            
            result = func(*args, **kwargs)
            return result
            
        except Exception as e:
            success = False
            error_message = str(e)
            raise
            
        finally:
            execution_time = time.time() - start_time
            
            metric = PerformanceMetric(
                function_name=func.__name__,
                execution_time=execution_time,
                timestamp=time.time(),
                success=success,
                error_message=error_message,
                metadata=metadata
            )
            
            performance_monitor.record_metric(metric)
    
    return wrapper

class CacheManager:
    """Manages caching for expensive operations"""
    
    def __init__(self, max_size: int = 100):
        self.cache: Dict[str, Any] = {}
        self.access_times: Dict[str, float] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key in self.cache:
                self.access_times[key] = time.time()
                self.hits += 1
                return self.cache[key]
            else:
                self.misses += 1
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Set value in cache with optional TTL"""
        with self._lock:
            # Remove oldest entries if cache is full
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_oldest()
            
            self.cache[key] = value
            self.access_times[key] = time.time()
            
            # Store TTL if provided
            if ttl:
                self.cache[f"{key}_ttl"] = time.time() + ttl
    
    def _evict_oldest(self):
        """Evict the least recently used item"""
        if not self.access_times:
            return
        
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[oldest_key]
        del self.access_times[oldest_key]
    
    def is_expired(self, key: str) -> bool:
        """Check if a cached item has expired"""
        ttl_key = f"{key}_ttl"
        if ttl_key in self.cache:
            return time.time() > self.cache[ttl_key]
        return False
    
    def clear(self):
        """Clear all cached items"""
        with self._lock:
            self.cache.clear()
            self.access_times.clear()
            self.hits = 0
            self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate
            }

# Global cache manager instance
cache_manager = CacheManager()

def cached(ttl: Optional[float] = None, key_func: Optional[Callable] = None):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds
        key_func: Function to generate cache key from args/kwargs
        
    Returns:
        Decorated function with caching
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = "|".join(key_parts)
            
            # Check cache
            if not cache_manager.is_expired(cache_key):
                cached_result = cache_manager.get(cache_key)
                if cached_result is not None:
                    return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

class ResourceMonitor:
    """Monitors system resource usage"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
        self.peak_memory = 0
        
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss': memory_info.rss,  # Resident Set Size
                'vms': memory_info.vms,  # Virtual Memory Size
                'percent': process.memory_percent(),
                'available': psutil.virtual_memory().available
            }
        except ImportError:
            return {'error': 'psutil not available'}
    
    def get_cpu_usage(self) -> Dict[str, Any]:
        """Get current CPU usage"""
        try:
            import psutil
            return {
                'percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'load_avg': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
        except ImportError:
            return {'error': 'psutil not available'}
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get general system information"""
        try:
            import psutil
            return {
                'uptime': time.time() - self.start_time,
                'memory': self.get_memory_usage(),
                'cpu': self.get_cpu_usage(),
                'disk': {
                    'total': psutil.disk_usage('/').total,
                    'used': psutil.disk_usage('/').used,
                    'free': psutil.disk_usage('/').free
                }
            }
        except ImportError:
            return {'error': 'psutil not available'}

# Global resource monitor instance
resource_monitor = ResourceMonitor()

class PerformanceOptimizer:
    """Provides optimization recommendations based on performance data"""
    
    def __init__(self, performance_monitor: PerformanceMonitor):
        self.performance_monitor = performance_monitor
        self.logger = logging.getLogger(__name__)
    
    def analyze_performance(self) -> List[Dict[str, Any]]:
        """Analyze performance data and provide recommendations"""
        recommendations = []
        stats = self.performance_monitor.get_stats()
        
        for func_name, func_stats in stats.items():
            if func_stats['call_count'] < 5:  # Need enough data points
                continue
                
            # Check for slow functions
            if func_stats['avg_time'] > 2.0:  # 2 seconds threshold
                recommendations.append({
                    'type': 'slow_function',
                    'function': func_name,
                    'avg_time': func_stats['avg_time'],
                    'call_count': func_stats['call_count'],
                    'recommendation': f"Consider optimizing {func_name} - average time: {func_stats['avg_time']:.2f}s"
                })
            
            # Check for frequently called functions
            if func_stats['call_count'] > 100 and func_stats['avg_time'] > 0.1:
                recommendations.append({
                    'type': 'frequent_function',
                    'function': func_name,
                    'avg_time': func_stats['avg_time'],
                    'call_count': func_stats['call_count'],
                    'recommendation': f"Consider caching {func_name} - called {func_stats['call_count']} times"
                })
        
        return recommendations
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get a summary of optimization opportunities"""
        recommendations = self.analyze_performance()
        error_rate = self.performance_monitor.get_error_rate()
        
        return {
            'total_recommendations': len(recommendations),
            'error_rate': error_rate,
            'recommendations': recommendations,
            'cache_stats': cache_manager.get_stats(),
            'resource_info': resource_monitor.get_system_info()
        }

# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer(performance_monitor)

def get_performance_dashboard() -> Dict[str, Any]:
    """Get a comprehensive performance dashboard"""
    return {
        'performance_stats': performance_monitor.get_stats(),
        'cache_stats': cache_manager.get_stats(),
        'resource_info': resource_monitor.get_system_info(),
        'optimization_summary': performance_optimizer.get_optimization_summary(),
        'recent_metrics': [
            {
                'function_name': m.function_name,
                'execution_time': m.execution_time,
                'timestamp': m.timestamp,
                'success': m.success,
                'error_message': m.error_message
            }
            for m in performance_monitor.get_recent_metrics(20)
        ]
    }
