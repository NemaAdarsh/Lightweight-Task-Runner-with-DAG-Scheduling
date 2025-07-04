"""Unit tests for ConfigLoader class."""

import pytest
import json
import os
import tempfile

from task_runner.utils.config import ConfigLoader, ConfigValidator
from task_runner.core.dag import DAG
from task_runner.core.task import Task


class TestConfigLoader:
    """Test cases for ConfigLoader class."""
    
    def test_load_from_dict_basic(self, sample_dag_config):
        """Test loading DAG from dictionary."""
        dag = ConfigLoader.load_from_dict(sample_dag_config)
        
        assert isinstance(dag, DAG)
        assert dag.dag_id == "test_dag"
        assert dag.description == "Test DAG"
        assert dag.max_workers == 2
        assert dag.execution_mode == "threading"
        assert len(dag.tasks) == 2
    
    def test_load_from_json(self, config_file):
        """Test loading DAG from JSON file."""
        dag = ConfigLoader.load_from_json(config_file)
        
        assert isinstance(dag, DAG)
        assert dag.dag_id == "test_dag"
        assert len(dag.tasks) == 2
    
    def test_load_from_nonexistent_file(self):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_from_json("nonexistent.json")
    
    def test_load_from_invalid_json(self, temp_dir):
        """Test loading from invalid JSON file."""
        invalid_file = os.path.join(temp_dir, "invalid.json")
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            ConfigLoader.load_from_json(invalid_file)
    
    def test_load_missing_required_fields(self):
        """Test loading config with missing required fields."""
        # Missing dag_id
        config = {
            "tasks": []
        }
        
        with pytest.raises(ValueError, match="Missing required field.*dag_id"):
            ConfigLoader.load_from_dict(config)
        
        # Missing tasks
        config = {
            "dag_id": "test"
        }
        
        with pytest.raises(ValueError, match="Missing required field.*tasks"):
            ConfigLoader.load_from_dict(config)
    
    def test_load_invalid_tasks_format(self):
        """Test loading config with invalid tasks format."""
        config = {
            "dag_id": "test",
            "tasks": "invalid"  # Should be list
        }
        
        with pytest.raises(ValueError, match="'tasks' must be a list"):
            ConfigLoader.load_from_dict(config)
    
    def test_parse_python_task_success(self):
        """Test parsing valid Python task."""
        task_config = {
            "task_id": "python_task",
            "task_type": "python",
            "function": "examples.tasks.hello_world",
            "args": ["test"],
            "kwargs": {"key": "value"},
            "retries": 2,
            "timeout": 30,
            "dependencies": ["dep1"]
        }
        
        task = ConfigLoader._parse_task(task_config)
        
        assert isinstance(task, Task)
        assert task.task_id == "python_task"
        assert task.task_type == "python"
        assert task.function == "examples.tasks.hello_world"
        assert task.args == ["test"]
        assert task.function_kwargs == {"key": "value"}
        assert task.retries == 2
        assert task.timeout == 30
        assert task.dependencies == ["dep1"]
    
    def test_parse_shell_task_success(self):
        """Test parsing valid shell task."""
        task_config = {
            "task_id": "shell_task",
            "task_type": "shell",
            "command": "echo hello",
            "retries": 1,
            "timeout": 10,
            "dependencies": []
        }
        
        task = ConfigLoader._parse_task(task_config)
        
        assert isinstance(task, Task)
        assert task.task_id == "shell_task"
        assert task.task_type == "shell"
        assert task.command == "echo hello"
        assert task.retries == 1
        assert task.timeout == 10
        assert task.dependencies == []
    
    def test_parse_task_missing_task_id(self):
        """Test parsing task without task_id."""
        task_config = {
            "task_type": "python",
            "function": "test.func"
        }
        
        with pytest.raises(ValueError, match="Missing required field.*task_id"):
            ConfigLoader._parse_task(task_config)
    
    def test_parse_task_missing_task_type(self):
        """Test parsing task without task_type."""
        task_config = {
            "task_id": "test",
            "function": "test.func"
        }
        
        with pytest.raises(ValueError, match="Missing required field.*task_type"):
            ConfigLoader._parse_task(task_config)
    
    def test_parse_python_task_missing_function(self):
        """Test parsing Python task without function."""
        task_config = {
            "task_id": "test",
            "task_type": "python"
        }
        
        with pytest.raises(ValueError, match="Python task.*must specify 'function'"):
            ConfigLoader._parse_task(task_config)
    
    def test_parse_shell_task_missing_command(self):
        """Test parsing shell task without command."""
        task_config = {
            "task_id": "test",
            "task_type": "shell"
        }
        
        with pytest.raises(ValueError, match="Shell task.*must specify 'command'"):
            ConfigLoader._parse_task(task_config)
    
    def test_parse_task_invalid_function_format(self):
        """Test parsing task with invalid function format."""
        task_config = {
            "task_id": "test",
            "task_type": "python",
            "function": "invalid_format"  # No dot
        }
        
        with pytest.raises(ValueError, match="function must be in format 'module.function'"):
            ConfigLoader._parse_task(task_config)
    
    def test_parse_task_invalid_dependencies(self):
        """Test parsing task with invalid dependencies format."""
        task_config = {
            "task_id": "test",
            "task_type": "python",
            "function": "test.func",
            "dependencies": "invalid"  # Should be list
        }
        
        with pytest.raises(ValueError, match="dependencies must be a list"):
            ConfigLoader._parse_task(task_config)
    
    def test_parse_task_unsupported_type(self):
        """Test parsing task with unsupported type."""
        task_config = {
            "task_id": "test",
            "task_type": "unsupported",
            "function": "test.func"
        }
        
        with pytest.raises(ValueError, match="unsupported task type"):
            ConfigLoader._parse_task(task_config)
    
    def test_validate_config_success(self, sample_dag_config):
        """Test successful config validation."""
        errors = ConfigLoader.validate_config(sample_dag_config)
        assert errors == []
    
    def test_validate_config_with_errors(self):
        """Test config validation with errors."""
        invalid_config = {
            "dag_id": "test",
            "tasks": [
                {
                    "task_id": "test",
                    "task_type": "invalid"
                }
            ]
        }
        
        errors = ConfigLoader.validate_config(invalid_config)
        assert len(errors) > 0
    
    def test_save_to_json(self, temp_dir, sample_dag_config):
        """Test saving DAG to JSON file."""
        dag = ConfigLoader.load_from_dict(sample_dag_config)
        output_file = os.path.join(temp_dir, "output.json")
        
        ConfigLoader.save_to_json(dag, output_file)
        
        assert os.path.exists(output_file)
        
        # Load and verify
        with open(output_file, 'r') as f:
            saved_config = json.load(f)
        
        assert saved_config["dag_id"] == "test_dag"
        assert len(saved_config["tasks"]) == 2


class TestConfigValidator:
    """Test cases for ConfigValidator class."""
    
    def test_validate_json_file_success(self, config_file):
        """Test successful JSON file validation."""
        errors = ConfigValidator.validate_json_file(config_file)
        assert errors == []
    
    def test_validate_json_file_not_found(self):
        """Test validation of non-existent file."""
        errors = ConfigValidator.validate_json_file("nonexistent.json")
        assert len(errors) == 1
        assert "not found" in errors[0]
    
    def test_validate_json_file_invalid_json(self, temp_dir):
        """Test validation of invalid JSON file."""
        invalid_file = os.path.join(temp_dir, "invalid.json")
        with open(invalid_file, 'w') as f:
            f.write("{ invalid }")
        
        errors = ConfigValidator.validate_json_file(invalid_file)
        assert len(errors) == 1
        assert "Invalid JSON" in errors[0]
    
    def test_validate_task_function_success(self):
        """Test successful function validation."""
        # This should work if the module exists
        result = ConfigValidator.validate_task_function("tests.conftest.simple_test_function")
        assert result is True
    
    def test_validate_task_function_failure(self):
        """Test function validation failure."""
        result = ConfigValidator.validate_task_function("nonexistent.module.function")
        assert result is False
        
        result = ConfigValidator.validate_task_function("invalid_format")
        assert result is False
