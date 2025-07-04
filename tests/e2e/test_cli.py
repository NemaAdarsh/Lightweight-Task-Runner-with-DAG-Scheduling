"""End-to-end tests using the CLI interface."""

import pytest
import json
import os
import subprocess
import tempfile
from pathlib import Path

from task_runner.utils import ConfigLoader


class TestCLI:
    """End-to-end tests for CLI interface."""
    
    @pytest.fixture
    def cli_config_file(self, temp_dir):
        """Create a CLI test configuration file."""
        config = {
            "dag_id": "cli_test",
            "description": "CLI test DAG",
            "max_workers": 2,
            "execution_mode": "threading",
            "tasks": [
                {
                    "task_id": "hello_task",
                    "task_type": "python",
                    "function": "examples.tasks.hello_world",
                    "args": ["CLI Test"],
                    "retries": 1,
                    "timeout": 30,
                    "dependencies": []
                },
                {
                    "task_id": "echo_task",
                    "task_type": "shell",
                    "command": "echo 'CLI shell test'",
                    "retries": 0,
                    "timeout": 10,
                    "dependencies": ["hello_task"]
                }
            ]
        }
        
        config_file = os.path.join(temp_dir, "cli_test.json")
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config_file
    
    def test_cli_validate_success(self, cli_config_file):
        """Test successful config validation via CLI."""
        result = subprocess.run([
            "python", "-m", "task_runner.cli", "validate",
            "--config", cli_config_file
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Configuration is valid" in result.stdout
    
    def test_cli_validate_failure(self, temp_dir):
        """Test config validation failure via CLI."""
        # Create invalid config
        invalid_config = {
            "dag_id": "invalid",
            "tasks": [
                {
                    "task_id": "invalid_task",
                    "task_type": "invalid_type"
                }
            ]
        }
        
        config_file = os.path.join(temp_dir, "invalid.json")
        with open(config_file, 'w') as f:
            json.dump(invalid_config, f)
        
        result = subprocess.run([
            "python", "-m", "task_runner.cli", "validate",
            "--config", config_file
        ], capture_output=True, text=True)
        
        assert result.returncode == 1
        assert "validation error" in result.stdout.lower()
    
    def test_cli_visualize(self, cli_config_file):
        """Test DAG visualization via CLI."""
        result = subprocess.run([
            "python", "-m", "task_runner.cli", "visualize",
            "--config", cli_config_file
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "cli_test" in result.stdout
        assert "hello_task" in result.stdout
        assert "echo_task" in result.stdout
    
    def test_cli_visualize_tree_style(self, cli_config_file):
        """Test tree-style DAG visualization via CLI."""
        result = subprocess.run([
            "python", "-m", "task_runner.cli", "visualize",
            "--config", cli_config_file,
            "--style", "tree"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "cli_test" in result.stdout
    
    def test_cli_run_success(self, cli_config_file):
        """Test successful DAG execution via CLI."""
        result = subprocess.run([
            "python", "-m", "task_runner.cli", "run",
            "--config", cli_config_file
        ], capture_output=True, text=True, timeout=30)
        
        assert result.returncode == 0
        assert "Starting execution" in result.stdout
        assert "Execution completed" in result.stdout
    
    def test_cli_run_with_visualization(self, cli_config_file):
        """Test DAG execution with visualization via CLI."""
        # This test would require user interaction, so we'll skip actual execution
        # and just test the command structure
        result = subprocess.run([
            "python", "-m", "task_runner.cli", "run",
            "--config", cli_config_file,
            "--visualize"
        ], input="n\n", capture_output=True, text=True, timeout=10)
        
        # Should show visualization and then cancel
        assert "DAG Visualization" in result.stdout
        assert "Execution cancelled" in result.stdout
    
    def test_cli_run_nonexistent_config(self):
        """Test CLI run with non-existent config file."""
        result = subprocess.run([
            "python", "-m", "task_runner.cli", "run",
            "--config", "nonexistent.json"
        ], capture_output=True, text=True)
        
        assert result.returncode == 2  # Click error for missing file
    
    def test_cli_help(self):
        """Test CLI help output."""
        result = subprocess.run([
            "python", "-m", "task_runner.cli", "--help"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Lightweight Task Runner" in result.stdout
        assert "run" in result.stdout
        assert "validate" in result.stdout
        assert "visualize" in result.stdout
    
    def test_cli_run_help(self):
        """Test CLI run command help."""
        result = subprocess.run([
            "python", "-m", "task_runner.cli", "run", "--help"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "--config" in result.stdout
        assert "--visualize" in result.stdout
        assert "--max-workers" in result.stdout
    
    def test_cli_verbose_logging(self, cli_config_file):
        """Test CLI with verbose logging."""
        result = subprocess.run([
            "python", "-m", "task_runner.cli", "--verbose",
            "validate", "--config", cli_config_file
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        # With verbose, we should see more detailed output
        assert "Configuration is valid" in result.stdout
    
    def test_cli_status_command(self):
        """Test CLI status command."""
        result = subprocess.run([
            "python", "-m", "task_runner.cli", "status",
            "--dag-id", "test_dag"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Status checking" in result.stdout
    
    def test_cli_list_command(self):
        """Test CLI list command."""
        result = subprocess.run([
            "python", "-m", "task_runner.cli", "list"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Listing DAGs" in result.stdout
    
    def test_cli_logs_command(self, temp_dir):
        """Test CLI logs command."""
        # Create a dummy log file
        log_dir = os.path.join(temp_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, "test_dag_20240101_120000.log")
        with open(log_file, 'w') as f:
            f.write("Test log entry\n")
        
        result = subprocess.run([
            "python", "-m", "task_runner.cli", "logs",
            "--log-dir", log_dir
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Test log entry" in result.stdout


class TestEndToEnd:
    """Complete end-to-end workflow tests."""
    
    def test_complete_workflow(self, temp_dir):
        """Test complete workflow from config creation to execution."""
        # Step 1: Create a complete DAG configuration
        config = {
            "dag_id": "e2e_workflow",
            "description": "End-to-end workflow test",
            "max_workers": 2,
            "execution_mode": "threading",
            "tasks": [
                {
                    "task_id": "init_task",
                    "task_type": "python",
                    "function": "examples.tasks.hello_world",
                    "args": ["E2E Test"],
                    "retries": 1,
                    "timeout": 30,
                    "dependencies": []
                },
                {
                    "task_id": "data_task",
                    "task_type": "python",
                    "function": "examples.tasks.process_data",
                    "args": ["test_data"],
                    "kwargs": {"multiplier": 2},
                    "retries": 2,
                    "timeout": 60,
                    "dependencies": ["init_task"]
                },
                {
                    "task_id": "validation_task",
                    "task_type": "python",
                    "function": "examples.tasks.validate_output",
                    "args": ["Processed: test_data x2"],
                    "retries": 1,
                    "timeout": 30,
                    "dependencies": ["data_task"]
                },
                {
                    "task_id": "cleanup_task",
                    "task_type": "shell",
                    "command": "echo 'Workflow completed successfully'",
                    "retries": 0,
                    "timeout": 10,
                    "dependencies": ["validation_task"]
                }
            ]
        }
        
        config_file = os.path.join(temp_dir, "e2e_workflow.json")
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Step 2: Validate the configuration
        validate_result = subprocess.run([
            "python", "-m", "task_runner.cli", "validate",
            "--config", config_file
        ], capture_output=True, text=True)
        
        assert validate_result.returncode == 0
        
        # Step 3: Visualize the DAG
        visualize_result = subprocess.run([
            "python", "-m", "task_runner.cli", "visualize",
            "--config", config_file
        ], capture_output=True, text=True)
        
        assert visualize_result.returncode == 0
        assert "e2e_workflow" in visualize_result.stdout
        
        # Step 4: Execute the DAG
        run_result = subprocess.run([
            "python", "-m", "task_runner.cli", "run",
            "--config", config_file
        ], capture_output=True, text=True, timeout=60)
        
        assert run_result.returncode == 0
        assert "Execution completed" in run_result.stdout
    
    def test_workflow_with_failure_handling(self, temp_dir):
        """Test workflow with intentional failures and retry logic."""
        config = {
            "dag_id": "failure_workflow",
            "description": "Workflow with failure handling",
            "max_workers": 1,
            "execution_mode": "threading",
            "tasks": [
                {
                    "task_id": "reliable_task",
                    "task_type": "python",
                    "function": "examples.tasks.hello_world",
                    "args": ["Reliable"],
                    "retries": 0,
                    "timeout": 10,
                    "dependencies": []
                },
                {
                    "task_id": "flaky_task",
                    "task_type": "python",
                    "function": "examples.tasks.failing_task",
                    "kwargs": {"failure_rate": 0.8},
                    "retries": 3,
                    "timeout": 15,
                    "dependencies": ["reliable_task"]
                },
                {
                    "task_id": "cleanup_task",
                    "task_type": "shell",
                    "command": "echo 'Cleanup after failure'",
                    "retries": 0,
                    "timeout": 5,
                    "dependencies": ["flaky_task"]
                }
            ]
        }
        
        config_file = os.path.join(temp_dir, "failure_workflow.json")
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Execute the DAG (may fail due to flaky task)
        run_result = subprocess.run([
            "python", "-m", "task_runner.cli", "run",
            "--config", config_file
        ], capture_output=True, text=True, timeout=60)
        
        # Either succeeds (if flaky task eventually passes) or fails gracefully
        assert run_result.returncode in [0, 1]
        assert "Starting execution" in run_result.stdout
    
    def test_shell_command_workflow(self, temp_dir):
        """Test workflow using primarily shell commands."""
        config = {
            "dag_id": "shell_workflow",
            "description": "Shell command workflow",
            "max_workers": 2,
            "execution_mode": "threading",
            "tasks": [
                {
                    "task_id": "create_dir",
                    "task_type": "shell",
                    "command": f"mkdir -p {temp_dir}/output",
                    "retries": 1,
                    "timeout": 10,
                    "dependencies": []
                },
                {
                    "task_id": "create_file1",
                    "task_type": "shell",
                    "command": f"echo 'File 1 content' > {temp_dir}/output/file1.txt",
                    "retries": 1,
                    "timeout": 10,
                    "dependencies": ["create_dir"]
                },
                {
                    "task_id": "create_file2",
                    "task_type": "shell",
                    "command": f"echo 'File 2 content' > {temp_dir}/output/file2.txt",
                    "retries": 1,
                    "timeout": 10,
                    "dependencies": ["create_dir"]
                },
                {
                    "task_id": "combine_files",
                    "task_type": "shell",
                    "command": f"cat {temp_dir}/output/file1.txt {temp_dir}/output/file2.txt > {temp_dir}/output/combined.txt",
                    "retries": 1,
                    "timeout": 10,
                    "dependencies": ["create_file1", "create_file2"]
                }
            ]
        }
        
        config_file = os.path.join(temp_dir, "shell_workflow.json")
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Execute the workflow
        run_result = subprocess.run([
            "python", "-m", "task_runner.cli", "run",
            "--config", config_file
        ], capture_output=True, text=True, timeout=30)
        
        assert run_result.returncode == 0
        
        # Verify files were created
        combined_file = os.path.join(temp_dir, "output", "combined.txt")
        assert os.path.exists(combined_file)
        
        with open(combined_file, 'r') as f:
            content = f.read()
            assert "File 1 content" in content
            assert "File 2 content" in content
