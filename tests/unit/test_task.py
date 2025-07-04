"""Unit tests for Task class."""

import pytest
import time
from datetime import datetime

from task_runner.core.task import Task
from task_runner.core.state import TaskState, TaskResult


class TestTask:
    """Test cases for Task class."""
    
    def test_task_creation(self):
        """Test basic task creation."""
        task = Task(
            task_id="test_task",
            task_type="python",
            function="tests.conftest.simple_test_function",
            retries=2,
            timeout=30
        )
        
        assert task.task_id == "test_task"
        assert task.task_type == "python"
        assert task.retries == 2
        assert task.timeout == 30
        assert task.state == TaskState.PENDING
        assert task.current_attempt == 0
    
    def test_invalid_task_type(self):
        """Test task creation with invalid type."""
        with pytest.raises(ValueError, match="Invalid task type"):
            Task(
                task_id="test_task",
                task_type="invalid",
                command="echo test"
            )
    
    def test_python_task_missing_function(self):
        """Test Python task without function parameter."""
        with pytest.raises(ValueError, match="Python tasks must specify a 'function' parameter"):
            Task(
                task_id="test_task",
                task_type="python"
            )
    
    def test_shell_task_missing_command(self):
        """Test shell task without command parameter."""
        with pytest.raises(ValueError, match="Shell tasks must specify a 'command' parameter"):
            Task(
                task_id="test_task",
                task_type="shell"
            )
    
    def test_python_task_execution(self):
        """Test successful Python task execution."""
        task = Task(
            task_id="test_task",
            task_type="python",
            function="tests.conftest.simple_test_function",
            args=["hello"]
        )
        
        result = task.execute()
        
        assert isinstance(result, TaskResult)
        assert result.task_id == "test_task"
        assert result.state == TaskState.SUCCESS
        assert result.return_value == "Test result: hello"
        assert result.error is None
        assert task.state == TaskState.SUCCESS
    
    def test_shell_task_execution(self):
        """Test successful shell task execution."""
        task = Task(
            task_id="shell_task",
            task_type="shell",
            command="echo 'Hello Shell'"
        )
        
        result = task.execute()
        
        assert isinstance(result, TaskResult)
        assert result.task_id == "shell_task"
        assert result.state == TaskState.SUCCESS
        assert "Hello Shell" in result.return_value
        assert result.error is None
    
    def test_task_failure(self):
        """Test task failure handling."""
        task = Task(
            task_id="failing_task",
            task_type="python",
            function="tests.conftest.failing_test_function"
        )
        
        result = task.execute()
        
        assert result.state == TaskState.FAILED
        assert result.error is not None
        assert "Test failure" in str(result.error)
        assert task.state == TaskState.FAILED
    
    def test_task_retry_logic(self):
        """Test task retry mechanism."""
        task = Task(
            task_id="retry_task",
            task_type="python",
            function="tests.conftest.failing_test_function",
            retries=2
        )
        
        start_time = time.time()
        result = task.execute()
        end_time = time.time()
        
        assert result.state == TaskState.FAILED
        assert task.current_attempt == 3  # Initial attempt + 2 retries
        # Should have some delay due to exponential backoff
        assert end_time - start_time >= 1  # At least 1 second for retries
    
    def test_task_timeout(self):
        """Test task timeout handling."""
        task = Task(
            task_id="timeout_task",
            task_type="python",
            function="tests.conftest.slow_test_function",
            args=[2.0],  # 2 second delay
            timeout=1  # 1 second timeout
        )
        
        result = task.execute()
        
        assert result.state == TaskState.FAILED
        assert isinstance(result.error, TimeoutError)
        assert "timed out" in str(result.error)
    
    def test_task_with_dependencies(self):
        """Test task with dependencies."""
        task = Task(
            task_id="dependent_task",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["task_1", "task_2"]
        )
        
        assert task.dependencies == ["task_1", "task_2"]
    
    def test_task_reset(self):
        """Test task state reset."""
        task = Task(
            task_id="reset_task",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        # Execute task
        task.execute()
        assert task.state == TaskState.SUCCESS
        assert task.current_attempt == 1
        
        # Reset task
        task.reset()
        assert task.state == TaskState.PENDING
        assert task.current_attempt == 0
    
    def test_task_can_retry(self):
        """Test can_retry method."""
        task = Task(
            task_id="retry_test",
            task_type="python",
            function="tests.conftest.simple_test_function",
            retries=2
        )
        
        assert task.can_retry() is True
        
        task.current_attempt = 1
        assert task.can_retry() is True
        
        task.current_attempt = 2
        assert task.can_retry() is False
    
    def test_task_to_dict(self):
        """Test task serialization to dictionary."""
        task = Task(
            task_id="dict_task",
            task_type="python",
            function="tests.conftest.simple_test_function",
            args=["test"],
            retries=1,
            timeout=30,
            dependencies=["dep1"]
        )
        
        task_dict = task.to_dict()
        
        assert task_dict["task_id"] == "dict_task"
        assert task_dict["task_type"] == "python"
        assert task_dict["state"] == "pending"
        assert task_dict["retries"] == 1
        assert task_dict["timeout"] == 30
        assert task_dict["dependencies"] == ["dep1"]
        assert task_dict["function"] == "tests.conftest.simple_test_function"
        assert task_dict["args"] == ["test"]
    
    def test_task_repr(self):
        """Test task string representation."""
        task = Task(
            task_id="repr_task",
            task_type="shell",
            command="echo test"
        )
        
        repr_str = repr(task)
        assert "repr_task" in repr_str
        assert "shell" in repr_str
        assert "pending" in repr_str
