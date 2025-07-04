"""Integration tests for complete DAG execution."""

import pytest
import time
import threading
from unittest.mock import patch

from task_runner.core import DAG, Task, TaskRunner
from task_runner.core.state import DAGState, TaskState
from task_runner.utils import ConfigLoader


class TestDAGExecution:
    """Integration tests for DAG execution."""
    
    def test_simple_dag_execution(self, sample_dag_config):
        """Test execution of a simple DAG."""
        dag = ConfigLoader.load_from_dict(sample_dag_config)
        runner = TaskRunner(max_workers=2, execution_mode="threading")
        
        result = runner.run_dag(dag)
        
        assert result.state == DAGState.SUCCESS
        assert len(result.task_results) == 2
        assert result.success_rate == 1.0
        
        # Check individual task results
        for task_result in result.task_results.values():
            assert task_result.state == TaskState.SUCCESS
    
    def test_parallel_execution(self):
        """Test parallel execution of independent tasks."""
        dag = DAG(dag_id="parallel_test", max_workers=3)
        
        # Create three independent tasks
        for i in range(3):
            task = Task(
                task_id=f"parallel_task_{i}",
                task_type="python",
                function="tests.conftest.slow_test_function",
                args=[0.5]  # 0.5 second delay each
            )
            dag.add_task(task)
        
        runner = TaskRunner(max_workers=3, execution_mode="threading")
        
        start_time = time.time()
        result = runner.run_dag(dag)
        end_time = time.time()
        
        # Should complete in roughly 0.5 seconds (parallel) rather than 1.5 (sequential)
        assert end_time - start_time < 1.0
        assert result.state == DAGState.SUCCESS
        assert len(result.task_results) == 3
    
    def test_sequential_dependencies(self):
        """Test sequential execution with dependencies."""
        dag = DAG(dag_id="sequential_test")
        
        # Create chain of dependent tasks
        prev_task_id = None
        for i in range(3):
            task_id = f"seq_task_{i}"
            dependencies = [prev_task_id] if prev_task_id else []
            
            task = Task(
                task_id=task_id,
                task_type="python",
                function="tests.conftest.slow_test_function",
                args=[0.2],  # 0.2 second delay each
                dependencies=dependencies
            )
            dag.add_task(task)
            prev_task_id = task_id
        
        runner = TaskRunner(max_workers=3, execution_mode="threading")
        
        start_time = time.time()
        result = runner.run_dag(dag)
        end_time = time.time()
        
        # Should take at least 0.6 seconds (sequential)
        assert end_time - start_time >= 0.6
        assert result.state == DAGState.SUCCESS
        assert len(result.task_results) == 3
    
    def test_dag_with_task_failure(self):
        """Test DAG execution with task failure."""
        dag = DAG(dag_id="failure_test")
        
        # Successful task
        success_task = Task(
            task_id="success_task",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        # Failing task
        fail_task = Task(
            task_id="fail_task",
            task_type="python",
            function="tests.conftest.failing_test_function"
        )
        
        # Dependent task (should be skipped)
        dependent_task = Task(
            task_id="dependent_task",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["fail_task"]
        )
        
        dag.add_task(success_task)
        dag.add_task(fail_task)
        dag.add_task(dependent_task)
        
        runner = TaskRunner(max_workers=2, execution_mode="threading")
        result = runner.run_dag(dag)
        
        assert result.state == DAGState.PARTIAL_SUCCESS
        assert len(result.task_results) == 3
        
        # Check individual results
        assert result.task_results["success_task"].state == TaskState.SUCCESS
        assert result.task_results["fail_task"].state == TaskState.FAILED
        assert result.task_results["dependent_task"].state == TaskState.SKIPPED
    
    def test_dag_retry_logic(self):
        """Test DAG execution with retry logic."""
        dag = DAG(dag_id="retry_test")
        
        # Task that fails initially but might succeed on retry
        retry_task = Task(
            task_id="retry_task",
            task_type="python",
            function="tests.conftest.failing_test_function",
            retries=2
        )
        
        dag.add_task(retry_task)
        
        runner = TaskRunner(max_workers=1, execution_mode="threading")
        result = runner.run_dag(dag)
        
        # Should fail after retries
        assert result.state == DAGState.FAILED
        assert result.task_results["retry_task"].state == TaskState.FAILED
        assert result.task_results["retry_task"].attempt > 1
    
    def test_dag_timeout_handling(self):
        """Test DAG execution with task timeouts."""
        dag = DAG(dag_id="timeout_test")
        
        # Task that takes longer than timeout
        timeout_task = Task(
            task_id="timeout_task",
            task_type="python",
            function="tests.conftest.slow_test_function",
            args=[2.0],  # 2 second delay
            timeout=1  # 1 second timeout
        )
        
        dag.add_task(timeout_task)
        
        runner = TaskRunner(max_workers=1, execution_mode="threading")
        result = runner.run_dag(dag)
        
        assert result.state == DAGState.FAILED
        assert result.task_results["timeout_task"].state == TaskState.FAILED
        assert isinstance(result.task_results["timeout_task"].error, TimeoutError)
    
    def test_complex_dag_execution(self):
        """Test execution of a complex DAG with multiple patterns."""
        dag = DAG(dag_id="complex_test", max_workers=4)
        
        # Root tasks (parallel)
        root1 = Task(
            task_id="root1",
            task_type="python",
            function="tests.conftest.simple_test_function",
            args=["root1"]
        )
        
        root2 = Task(
            task_id="root2",
            task_type="python",
            function="tests.conftest.simple_test_function",
            args=["root2"]
        )
        
        # Middle layer (depends on roots)
        middle1 = Task(
            task_id="middle1",
            task_type="python",
            function="tests.conftest.simple_test_function",
            args=["middle1"],
            dependencies=["root1"]
        )
        
        middle2 = Task(
            task_id="middle2",
            task_type="python",
            function="tests.conftest.simple_test_function",
            args=["middle2"],
            dependencies=["root2"]
        )
        
        # Final task (depends on all middle tasks)
        final = Task(
            task_id="final",
            task_type="python",
            function="tests.conftest.simple_test_function",
            args=["final"],
            dependencies=["middle1", "middle2"]
        )
        
        dag.add_task(root1)
        dag.add_task(root2)
        dag.add_task(middle1)
        dag.add_task(middle2)
        dag.add_task(final)
        
        runner = TaskRunner(max_workers=4, execution_mode="threading")
        result = runner.run_dag(dag)
        
        assert result.state == DAGState.SUCCESS
        assert len(result.task_results) == 5
        assert result.success_rate == 1.0
        
        # Verify execution order was respected
        root1_end = result.task_results["root1"].end_time
        root2_end = result.task_results["root2"].end_time
        middle1_start = result.task_results["middle1"].start_time
        middle2_start = result.task_results["middle2"].start_time
        final_start = result.task_results["final"].start_time
        
        # Middle tasks should start after their dependencies
        assert middle1_start >= root1_end
        assert middle2_start >= root2_end
        
        # Final task should start after all middle tasks
        middle1_end = result.task_results["middle1"].end_time
        middle2_end = result.task_results["middle2"].end_time
        assert final_start >= max(middle1_end, middle2_end)
    
    def test_multiprocessing_execution(self):
        """Test DAG execution with multiprocessing."""
        dag = DAG(dag_id="multiprocessing_test", execution_mode="multiprocessing")
        
        # Create CPU-bound tasks
        for i in range(2):
            task = Task(
                task_id=f"cpu_task_{i}",
                task_type="python",
                function="tests.conftest.simple_test_function",
                args=[f"task_{i}"]
            )
            dag.add_task(task)
        
        runner = TaskRunner(max_workers=2, execution_mode="multiprocessing")
        result = runner.run_dag(dag)
        
        assert result.state == DAGState.SUCCESS
        assert len(result.task_results) == 2
    
    def test_empty_dag_execution(self):
        """Test execution of empty DAG."""
        dag = DAG(dag_id="empty_test")
        runner = TaskRunner(max_workers=1, execution_mode="threading")
        
        result = runner.run_dag(dag)
        
        assert result.state == DAGState.SUCCESS
        assert len(result.task_results) == 0
        assert result.success_rate == 0.0
    
    def test_single_task_dag(self):
        """Test execution of DAG with single task."""
        dag = DAG(dag_id="single_test")
        
        task = Task(
            task_id="only_task",
            task_type="python",
            function="tests.conftest.simple_test_function",
            args=["single"]
        )
        
        dag.add_task(task)
        
        runner = TaskRunner(max_workers=1, execution_mode="threading")
        result = runner.run_dag(dag)
        
        assert result.state == DAGState.SUCCESS
        assert len(result.task_results) == 1
        assert result.task_results["only_task"].state == TaskState.SUCCESS
    
    def test_dag_status_monitoring(self):
        """Test DAG status monitoring during execution."""
        dag = DAG(dag_id="monitoring_test")
        
        # Long-running task for monitoring
        task = Task(
            task_id="long_task",
            task_type="python",
            function="tests.conftest.slow_test_function",
            args=[1.0]  # 1 second delay
        )
        
        dag.add_task(task)
        
        runner = TaskRunner(max_workers=1, execution_mode="threading")
        
        # Start execution in background
        result = runner.run_dag(dag, blocking=False)
        
        # Monitor status
        initial_status = runner.get_dag_status("monitoring_test")
        assert initial_status is not None
        assert initial_status.state == DAGState.RUNNING
        
        # Wait for completion
        time.sleep(2.0)
        
        final_status = runner.get_dag_status("monitoring_test")
        # Status might be None if DAG completed and was cleaned up
        if final_status:
            assert final_status.state in [DAGState.SUCCESS, DAGState.FAILED]
