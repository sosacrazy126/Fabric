"""
Real-time execution monitoring service for pattern execution tracking.
Provides live progress updates, execution queuing, and system health monitoring.
"""
import time
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import threading
import queue
import streamlit as st

from utils.logging import logger
from utils.typing import RunResult, ChainStep


class ExecutionStatus(Enum):
    """Execution status enumeration."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class ExecutionMetrics:
    """Comprehensive execution metrics for monitoring."""
    execution_id: str
    pattern: str
    status: ExecutionStatus
    progress: float = 0.0  # 0.0 to 1.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    input_size: int = 0
    output_size: Optional[int] = None
    duration_ms: Optional[int] = None
    memory_usage_mb: Optional[float] = None
    error_message: Optional[str] = None
    user_id: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """System health status for all components."""
    fabric_cli_available: bool = False
    provider_status: Dict[str, bool] = field(default_factory=dict)
    model_availability: Dict[str, List[str]] = field(default_factory=dict)
    last_check: Optional[datetime] = None
    fabric_version: Optional[str] = None
    system_load: Optional[float] = None
    memory_usage_percent: Optional[float] = None


class ExecutionMonitor:
    """Thread-safe singleton execution monitor for tracking pattern executions."""
    
    _instance = None
    _lock = threading.Lock()
    _init_lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Thread-safe initialization
        with self._init_lock:
            if not hasattr(self, '_initialized'):
                self._executions: Dict[str, ExecutionMetrics] = {}
                self._execution_queue: queue.Queue = queue.Queue()
                self._system_health = SystemHealth()
                self._callbacks: Dict[str, List[Callable]] = {}
                self._max_history = 100  # Reduced from 1000 to prevent memory bloat
                self._cleanup_thread = None
                self._data_lock = threading.RLock()  # Reentrant lock for data operations
                self._initialized = True
                logger.info("ExecutionMonitor initialized")
                
                # Start periodic cleanup
                self._start_cleanup_timer()
    
    def create_execution(self, pattern: str, provider: str = None, 
                        model: str = None, input_size: int = 0) -> str:
        """Create a new execution tracking entry."""
        execution_id = str(uuid.uuid4())
        
        metrics = ExecutionMetrics(
            execution_id=execution_id,
            pattern=pattern,
            status=ExecutionStatus.QUEUED,
            provider=provider,
            model=model,
            input_size=input_size,
            start_time=datetime.now()
        )
        
        with self._data_lock:
            self._executions[execution_id] = metrics
            # Trigger cleanup if needed
            if len(self._executions) > self._max_history * 1.2:  # 20% buffer
                self.cleanup_old_executions()
        
        self._trigger_callbacks('execution_created', metrics)
        
        logger.info(f"Created execution tracking for {pattern} (ID: {execution_id})")
        return execution_id
    
    def start_execution(self, execution_id: str) -> bool:
        """Mark an execution as started."""
        if execution_id not in self._executions:
            logger.warning(f"Execution ID {execution_id} not found")
            return False
        
        metrics = self._executions[execution_id]
        metrics.status = ExecutionStatus.RUNNING
        metrics.start_time = datetime.now()
        metrics.progress = 0.1  # Initial progress
        
        self._trigger_callbacks('execution_started', metrics)
        logger.info(f"Started execution {execution_id}")
        return True
    
    def update_progress(self, execution_id: str, progress: float, 
                       estimated_completion: datetime = None) -> bool:
        """Update execution progress."""
        if execution_id not in self._executions:
            return False
        
        metrics = self._executions[execution_id]
        metrics.progress = max(0.0, min(1.0, progress))
        
        if estimated_completion:
            metrics.estimated_completion = estimated_completion
        
        self._trigger_callbacks('progress_updated', metrics)
        return True
    
    def complete_execution(self, execution_id: str, result: RunResult) -> bool:
        """Mark an execution as completed with results."""
        if execution_id not in self._executions:
            logger.warning(f"Execution ID {execution_id} not found for completion")
            return False
        
        metrics = self._executions[execution_id]
        metrics.status = ExecutionStatus.COMPLETED if result.success else ExecutionStatus.FAILED
        metrics.end_time = datetime.now()
        metrics.progress = 1.0
        metrics.duration_ms = result.duration_ms
        metrics.output_size = len(result.output) if result.output else 0
        
        if not result.success:
            metrics.error_message = result.error
        
        self._trigger_callbacks('execution_completed', metrics)
        logger.info(f"Completed execution {execution_id} - Success: {result.success}")
        return True
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        if execution_id not in self._executions:
            return False
        
        metrics = self._executions[execution_id]
        metrics.status = ExecutionStatus.CANCELLED
        metrics.end_time = datetime.now()
        
        self._trigger_callbacks('execution_cancelled', metrics)
        logger.info(f"Cancelled execution {execution_id}")
        return True
    
    def get_execution(self, execution_id: str) -> Optional[ExecutionMetrics]:
        """Get execution metrics by ID."""
        return self._executions.get(execution_id)
    
    def get_active_executions(self) -> List[ExecutionMetrics]:
        """Get all currently active (running) executions."""
        return [
            metrics for metrics in self._executions.values()
            if metrics.status in [ExecutionStatus.QUEUED, ExecutionStatus.RUNNING]
        ]
    
    def get_recent_executions(self, limit: int = 50) -> List[ExecutionMetrics]:
        """Get recent executions sorted by start time."""
        sorted_executions = sorted(
            self._executions.values(),
            key=lambda x: x.start_time or datetime.min,
            reverse=True
        )
        return sorted_executions[:limit]
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get comprehensive execution statistics."""
        executions = list(self._executions.values())
        
        if not executions:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "average_duration": 0.0,
                "active_count": 0
            }
        
        completed = [e for e in executions if e.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]]
        successful = [e for e in completed if e.status == ExecutionStatus.COMPLETED]
        active = self.get_active_executions()
        
        durations = [e.duration_ms for e in completed if e.duration_ms is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        
        return {
            "total_executions": len(executions),
            "success_rate": len(successful) / len(completed) if completed else 0.0,
            "average_duration": avg_duration,
            "active_count": len(active),
            "completed_count": len(completed),
            "failed_count": len([e for e in completed if e.status == ExecutionStatus.FAILED])
        }
    
    def register_callback(self, event_type: str, callback: Callable) -> None:
        """Register callback for execution events."""
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)
    
    def _trigger_callbacks(self, event_type: str, metrics: ExecutionMetrics) -> None:
        """Trigger registered callbacks for an event."""
        if event_type in self._callbacks:
            for callback in self._callbacks[event_type]:
                try:
                    callback(metrics)
                except Exception as e:
                    logger.error(f"Error in callback for {event_type}: {e}")
    
    def cleanup_old_executions(self) -> None:
        """Clean up old execution records to prevent memory bloat."""
        with self._data_lock:
            if len(self._executions) <= self._max_history:
                return
            
            # Keep only the most recent executions
            sorted_executions = sorted(
                self._executions.items(),
                key=lambda x: x[1].start_time or datetime.min,
                reverse=True
            )
            
            keep_executions = dict(sorted_executions[:self._max_history])
            removed_count = len(self._executions) - len(keep_executions)
            
            self._executions = keep_executions
            logger.info(f"Cleaned up {removed_count} old execution records")
    
    def update_system_health(self, health: SystemHealth) -> None:
        """Update system health status."""
        self._system_health = health
        self._trigger_callbacks('health_updated', health)
    
    def get_system_health(self) -> SystemHealth:
        """Get current system health status."""
        return self._system_health
    
    def _start_cleanup_timer(self) -> None:
        """Start periodic cleanup timer to prevent memory leaks."""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(300)  # Clean up every 5 minutes
                    self.cleanup_old_executions()
                    
                    # Also clean up old callbacks
                    self._cleanup_stale_callbacks()
                    
                except Exception as e:
                    logger.error(f"Cleanup worker error: {e}")
        
        import threading
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        logger.info("Started cleanup timer for memory leak prevention")
    
    def _cleanup_stale_callbacks(self) -> None:
        """Remove callbacks that may be holding references to dead objects."""
        for event_type in list(self._callbacks.keys()):
            # Keep only callbacks that are still valid (simple approach)
            valid_callbacks = []
            for callback in self._callbacks[event_type]:
                try:
                    # Test if callback is still callable and not a dead reference
                    if callable(callback):
                        valid_callbacks.append(callback)
                except:
                    # Skip invalid callbacks
                    pass
            
            self._callbacks[event_type] = valid_callbacks
            
            # Remove empty callback lists
            if not self._callbacks[event_type]:
                del self._callbacks[event_type]


# Singleton instance
_monitor = None

def get_execution_monitor() -> ExecutionMonitor:
    """Get singleton ExecutionMonitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = ExecutionMonitor()
    return _monitor


def track_execution(pattern: str, provider: str = None, model: str = None, 
                   input_size: int = 0) -> str:
    """Convenience function to create and track a new execution."""
    monitor = get_execution_monitor()
    return monitor.create_execution(pattern, provider, model, input_size)


def update_execution_progress(execution_id: str, progress: float) -> bool:
    """Convenience function to update execution progress."""
    monitor = get_execution_monitor()
    return monitor.update_progress(execution_id, progress)


def complete_execution(execution_id: str, result: RunResult) -> bool:
    """Convenience function to complete an execution."""
    monitor = get_execution_monitor()
    return monitor.complete_execution(execution_id, result)