"""Test configuration and fixtures."""

import pytest
import tempfile
import os
import json
from typing import Dict, Any

from task_runner.core import Task, DAG, TaskRunner
from task_runner.utils import ConfigLoader


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_task_config():
    """Sample task configuration for testing."""
    return {
        "task_id": "test_task",
        "task_type": "python",
        "function": "examples.tasks.hello_world",
        "args": ["Test"],
        "retries": 2,
        "timeout": 30,
        "dependencies": []
    }


@pytest.fixture
def sample_dag_config():
    """Sample DAG configuration for testing."""
    return {
        "dag_id": "test_dag",
        "description": "Test DAG",
        "max_workers": 2,
        "execution_mode": "threading",
        "tasks": [
            {
                "task_id": "task_1",
                "task_type": "python",
                "function": "examples.tasks.hello_world",
                "args": ["Task 1"],
                "retries": 1,
                "timeout": 10,
                "dependencies": []
            },
            {
                "task_id": "task_2", 
                "task_type": "python",
                "function": "examples.tasks.hello_world",
                "args": ["Task 2"],
                "retries": 1,
                "timeout": 10,
                "dependencies": ["task_1"]
            }
        ]
    }


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        task_id="test_task",
        task_type="python",
        function="examples.tasks.hello_world",
        args=["Test"],
        retries=1,
        timeout=10
    )


@pytest.fixture
def sample_dag(sample_dag_config):
    """Create a sample DAG for testing."""
    return ConfigLoader.load_from_dict(sample_dag_config)


@pytest.fixture
def task_runner():
    """Create a task runner for testing."""
    return TaskRunner(max_workers=2, execution_mode="threading")


@pytest.fixture
def config_file(temp_dir, sample_dag_config):
    """Create a temporary configuration file."""
    config_path = os.path.join(temp_dir, "test_dag.json")
    with open(config_path, 'w') as f:
        json.dump(sample_dag_config, f)
    return config_path


def simple_test_function(message: str = "test") -> str:
    """Simple function for testing."""
    return f"Test result: {message}"


def failing_test_function():
    """Function that always fails for testing."""
    raise RuntimeError("Test failure")


def slow_test_function(delay: float = 0.1) -> str:
    """Function with configurable delay for testing."""
    import time
    time.sleep(delay)
    return f"Completed after {delay} seconds"
