import importlib
import subprocess
import threading
import time
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Union
from .state import TaskState, TaskResult


logger = logging.getLogger(__name__)


class Task:
    """
    Represents an individual task in the DAG.
    
    A task can be either a Python function or a shell command.
    It includes retry logic, timeout handling, and state management.
    """
    
    def __init__(
        self,
        task_id: str,
        task_type: str,
        retries: int = 0,
        timeout: Optional[int] = None,
        dependencies: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize a new task.
        
        Args:
            task_id: Unique identifier for the task
            task_type: Type of task ('python' or 'shell')
            retries: Number of retry attempts
            timeout: Task timeout in seconds
            dependencies: List of task IDs this task depends on
            **kwargs: Additional task-specific parameters
        """
        self.task_id = task_id
        self.task_type = task_type.lower()
        self.retries = retries
        self.timeout = timeout
        self.dependencies = dependencies or []
        self.state = TaskState.PENDING
        self.current_attempt = 0
        self.kwargs = kwargs
        
        # Validate task type
        if self.task_type not in ['python', 'shell']:
            raise ValueError(f"Invalid task type: {self.task_type}")
        
        # Extract task-specific parameters
        if self.task_type == 'python':
            self.function = kwargs.get('function')
            self.args = kwargs.get('args', [])
            self.function_kwargs = kwargs.get('kwargs', {})
            if not self.function:
                raise ValueError("Python tasks must specify a 'function' parameter")
        elif self.task_type == 'shell':
            self.command = kwargs.get('command')
            if not self.command:
                raise ValueError("Shell tasks must specify a 'command' parameter")
    
    def execute(self) -> TaskResult:
        """
        Execute the task with retry logic and timeout handling.
        
        Returns:
            TaskResult: Result of task execution
        """
        logger.info(f"Starting execution of task: {self.task_id}")
        
        while self.current_attempt <= self.retries:
            self.current_attempt += 1
            self.state = TaskState.RUNNING
            
            start_time = datetime.now()
            
            try:
                if self.task_type == 'python':
                    result = self._execute_python_task()
                else:
                    result = self._execute_shell_task()
                
                end_time = datetime.now()
                self.state = TaskState.SUCCESS
                
                logger.info(
                    f"Task {self.task_id} completed successfully on attempt {self.current_attempt}"
                )
                
                return TaskResult(
                    task_id=self.task_id,
                    state=TaskState.SUCCESS,
                    start_time=start_time,
                    end_time=end_time,
                    return_value=result,
                    attempt=self.current_attempt
                )
                
            except Exception as e:
                end_time = datetime.now()
                logger.error(
                    f"Task {self.task_id} failed on attempt {self.current_attempt}: {str(e)}"
                )
                
                if self.current_attempt <= self.retries:
                    wait_time = min(2 ** (self.current_attempt - 1), 60)
                    logger.info(f"Retrying task {self.task_id} in {wait_time} seconds")
                    time.sleep(wait_time)
                else:
                    self.state = TaskState.FAILED
                    return TaskResult(
                        task_id=self.task_id,
                        state=TaskState.FAILED,
                        start_time=start_time,
                        end_time=end_time,
                        error=e,
                        attempt=self.current_attempt
                    )
    
    def _execute_python_task(self) -> Any:
        """Execute a Python function task."""
        module_path, function_name = self.function.rsplit('.', 1)
        module = importlib.import_module(module_path)
        func = getattr(module, function_name)
        
        if self.timeout:
            return self._execute_with_timeout(
                lambda: func(*self.args, **self.function_kwargs)
            )
        else:
            return func(*self.args, **self.function_kwargs)
    
    def _execute_shell_task(self) -> str:
        """Execute a shell command task."""
        if self.timeout:
            return self._execute_with_timeout(
                lambda: subprocess.run(
                    self.command,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True
                ).stdout
            )
        else:
            result = subprocess.run(
                self.command,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout
    
    def _execute_with_timeout(self, func: Callable) -> Any:
        """Execute a function with timeout handling."""
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = func()
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.timeout)
        
        if thread.is_alive():
            raise TimeoutError(f"Task {self.task_id} timed out after {self.timeout} seconds")
        
        if exception[0]:
            raise exception[0]
        
        return result[0]
    
    def can_retry(self) -> bool:
        """Check if the task can be retried."""
        return self.current_attempt < self.retries
    
    def reset(self):
        """Reset task state for re-execution."""
        self.state = TaskState.PENDING
        self.current_attempt = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "state": self.state.value,
            "retries": self.retries,
            "timeout": self.timeout,
            "dependencies": self.dependencies,
            "current_attempt": self.current_attempt,
            **self.kwargs
        }
    
    def __repr__(self) -> str:
        return f"Task(id={self.task_id}, type={self.task_type}, state={self.state.value})"
