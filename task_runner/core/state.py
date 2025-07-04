from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class TaskState(Enum):
    """Enumeration for task execution states."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class DAGState(Enum):
    """Enumeration for DAG execution states."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"


class TaskResult:
    """Container for task execution results."""
    
    def __init__(
        self,
        task_id: str,
        state: TaskState,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        return_value: Any = None,
        error: Optional[Exception] = None,
        attempt: int = 1
    ):
        self.task_id = task_id
        self.state = state
        self.start_time = start_time
        self.end_time = end_time
        self.return_value = return_value
        self.error = error
        self.attempt = attempt
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate task execution duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def success(self) -> bool:
        """Check if task completed successfully."""
        return self.state == TaskState.SUCCESS
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            "task_id": self.task_id,
            "state": self.state.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "return_value": str(self.return_value) if self.return_value else None,
            "error": str(self.error) if self.error else None,
            "attempt": self.attempt
        }


class DAGResult:
    """Container for DAG execution results."""
    
    def __init__(self, dag_id: str):
        self.dag_id = dag_id
        self.state = DAGState.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.task_results: Dict[str, TaskResult] = {}
    
    def add_task_result(self, result: TaskResult):
        """Add a task result to the DAG result."""
        self.task_results[result.task_id] = result
    
    def update_state(self):
        """Update DAG state based on task results."""
        if not self.task_results:
            self.state = DAGState.PENDING
            return
        
        states = [result.state for result in self.task_results.values()]
        
        if all(state == TaskState.SUCCESS for state in states):
            self.state = DAGState.SUCCESS
        elif any(state == TaskState.FAILED for state in states):
            success_count = sum(1 for state in states if state == TaskState.SUCCESS)
            if success_count > 0:
                self.state = DAGState.PARTIAL_SUCCESS
            else:
                self.state = DAGState.FAILED
        elif any(state == TaskState.RUNNING for state in states):
            self.state = DAGState.RUNNING
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate total DAG execution duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of tasks."""
        if not self.task_results:
            return 0.0
        
        successful_tasks = sum(
            1 for result in self.task_results.values()
            if result.state == TaskState.SUCCESS
        )
        return successful_tasks / len(self.task_results)
    
    def get_failed_tasks(self) -> Dict[str, TaskResult]:
        """Get all failed task results."""
        return {
            task_id: result for task_id, result in self.task_results.items()
            if result.state == TaskState.FAILED
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            "dag_id": self.dag_id,
            "state": self.state.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "success_rate": self.success_rate,
            "task_results": {
                task_id: result.to_dict() 
                for task_id, result in self.task_results.items()
            }
        }
