"""Unit tests for DAG class."""

import pytest
import networkx as nx

from task_runner.core.dag import DAG
from task_runner.core.task import Task
from task_runner.core.state import DAGState, TaskState


class TestDAG:
    """Test cases for DAG class."""
    
    def test_dag_creation(self):
        """Test basic DAG creation."""
        dag = DAG(
            dag_id="test_dag",
            description="Test DAG",
            max_workers=4,
            execution_mode="threading"
        )
        
        assert dag.dag_id == "test_dag"
        assert dag.description == "Test DAG"
        assert dag.max_workers == 4
        assert dag.execution_mode == "threading"
        assert dag.state == DAGState.PENDING
        assert len(dag.tasks) == 0
    
    def test_invalid_execution_mode(self):
        """Test DAG creation with invalid execution mode."""
        with pytest.raises(ValueError, match="Invalid execution mode"):
            DAG(
                dag_id="test_dag",
                execution_mode="invalid"
            )
    
    def test_add_task(self):
        """Test adding tasks to DAG."""
        dag = DAG(dag_id="test_dag")
        
        task1 = Task(
            task_id="task1",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        task2 = Task(
            task_id="task2",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["task1"]
        )
        
        dag.add_task(task1)
        dag.add_task(task2)
        
        assert len(dag.tasks) == 2
        assert "task1" in dag.tasks
        assert "task2" in dag.tasks
        assert dag.graph.has_edge("task1", "task2")
    
    def test_add_duplicate_task(self):
        """Test adding task with duplicate ID."""
        dag = DAG(dag_id="test_dag")
        
        task1 = Task(
            task_id="duplicate",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        task2 = Task(
            task_id="duplicate",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        dag.add_task(task1)
        
        with pytest.raises(ValueError, match="Task with ID 'duplicate' already exists"):
            dag.add_task(task2)
    
    def test_remove_task(self):
        """Test removing tasks from DAG."""
        dag = DAG(dag_id="test_dag")
        
        task = Task(
            task_id="removable",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        dag.add_task(task)
        assert "removable" in dag.tasks
        
        dag.remove_task("removable")
        assert "removable" not in dag.tasks
        assert not dag.graph.has_node("removable")
    
    def test_remove_nonexistent_task(self):
        """Test removing non-existent task."""
        dag = DAG(dag_id="test_dag")
        
        with pytest.raises(KeyError, match="Task 'nonexistent' not found"):
            dag.remove_task("nonexistent")
    
    def test_get_task(self):
        """Test getting task by ID."""
        dag = DAG(dag_id="test_dag")
        
        task = Task(
            task_id="gettable",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        dag.add_task(task)
        
        retrieved_task = dag.get_task("gettable")
        assert retrieved_task is task
        
        missing_task = dag.get_task("missing")
        assert missing_task is None
    
    def test_dag_validation_success(self):
        """Test successful DAG validation."""
        dag = DAG(dag_id="valid_dag")
        
        task1 = Task(
            task_id="task1",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        task2 = Task(
            task_id="task2",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["task1"]
        )
        
        dag.add_task(task1)
        dag.add_task(task2)
        
        assert dag.validate() is True
    
    def test_dag_validation_cycle(self):
        """Test DAG validation with cycle detection."""
        dag = DAG(dag_id="cyclic_dag")
        
        task1 = Task(
            task_id="task1",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["task2"]
        )
        
        task2 = Task(
            task_id="task2",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["task1"]
        )
        
        dag.add_task(task1)
        dag.add_task(task2)
        
        with pytest.raises(ValueError, match="contains cycles"):
            dag.validate()
    
    def test_dag_validation_missing_dependency(self):
        """Test DAG validation with missing dependencies."""
        dag = DAG(dag_id="missing_dep_dag")
        
        task = Task(
            task_id="task1",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["missing_task"]
        )
        
        dag.add_task(task)
        
        with pytest.raises(ValueError, match="Missing dependencies"):
            dag.validate()
    
    def test_get_execution_order(self):
        """Test getting topological execution order."""
        dag = DAG(dag_id="ordered_dag")
        
        # Create a simple chain: task1 -> task2 -> task3
        task1 = Task(
            task_id="task1",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        task2 = Task(
            task_id="task2",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["task1"]
        )
        
        task3 = Task(
            task_id="task3",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["task2"]
        )
        
        dag.add_task(task1)
        dag.add_task(task2)
        dag.add_task(task3)
        
        execution_order = dag.get_execution_order()
        
        assert len(execution_order) == 3
        assert execution_order[0] == ["task1"]
        assert execution_order[1] == ["task2"]
        assert execution_order[2] == ["task3"]
    
    def test_get_execution_order_parallel(self):
        """Test execution order with parallel tasks."""
        dag = DAG(dag_id="parallel_dag")
        
        # Create parallel structure: task1 -> [task2, task3] -> task4
        task1 = Task(
            task_id="task1",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        task2 = Task(
            task_id="task2",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["task1"]
        )
        
        task3 = Task(
            task_id="task3",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["task1"]
        )
        
        task4 = Task(
            task_id="task4",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["task2", "task3"]
        )
        
        dag.add_task(task1)
        dag.add_task(task2)
        dag.add_task(task3)
        dag.add_task(task4)
        
        execution_order = dag.get_execution_order()
        
        assert len(execution_order) == 3
        assert execution_order[0] == ["task1"]
        assert set(execution_order[1]) == {"task2", "task3"}
        assert execution_order[2] == ["task4"]
    
    def test_get_root_tasks(self):
        """Test getting root tasks (no dependencies)."""
        dag = DAG(dag_id="root_dag")
        
        root1 = Task(
            task_id="root1",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        root2 = Task(
            task_id="root2",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        dependent = Task(
            task_id="dependent",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["root1"]
        )
        
        dag.add_task(root1)
        dag.add_task(root2)
        dag.add_task(dependent)
        
        root_tasks = dag.get_root_tasks()
        assert set(root_tasks) == {"root1", "root2"}
    
    def test_get_leaf_tasks(self):
        """Test getting leaf tasks (no dependents)."""
        dag = DAG(dag_id="leaf_dag")
        
        root = Task(
            task_id="root",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        leaf1 = Task(
            task_id="leaf1",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["root"]
        )
        
        leaf2 = Task(
            task_id="leaf2",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["root"]
        )
        
        dag.add_task(root)
        dag.add_task(leaf1)
        dag.add_task(leaf2)
        
        leaf_tasks = dag.get_leaf_tasks()
        assert set(leaf_tasks) == {"leaf1", "leaf2"}
    
    def test_get_task_dependencies(self):
        """Test getting all task dependencies."""
        dag = DAG(dag_id="dep_dag")
        
        # Create chain: task1 -> task2 -> task3
        task1 = Task(
            task_id="task1",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        task2 = Task(
            task_id="task2",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["task1"]
        )
        
        task3 = Task(
            task_id="task3",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["task2"]
        )
        
        dag.add_task(task1)
        dag.add_task(task2)
        dag.add_task(task3)
        
        # task3 should depend on both task1 and task2 (transitively)
        deps = dag.get_task_dependencies("task3")
        assert deps == {"task1", "task2"}
        
        # task2 should only depend on task1
        deps = dag.get_task_dependencies("task2")
        assert deps == {"task1"}
        
        # task1 should have no dependencies
        deps = dag.get_task_dependencies("task1")
        assert deps == set()
    
    def test_get_task_dependents(self):
        """Test getting all task dependents."""
        dag = DAG(dag_id="dependents_dag")
        
        # Create chain: task1 -> task2 -> task3
        task1 = Task(
            task_id="task1",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        task2 = Task(
            task_id="task2",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["task1"]
        )
        
        task3 = Task(
            task_id="task3",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["task2"]
        )
        
        dag.add_task(task1)
        dag.add_task(task2)
        dag.add_task(task3)
        
        # task1 should have both task2 and task3 as dependents
        dependents = dag.get_task_dependents("task1")
        assert dependents == {"task2", "task3"}
        
        # task2 should only have task3 as dependent
        dependents = dag.get_task_dependents("task2")
        assert dependents == {"task3"}
        
        # task3 should have no dependents
        dependents = dag.get_task_dependents("task3")
        assert dependents == set()
    
    def test_dag_reset(self):
        """Test DAG reset functionality."""
        dag = DAG(dag_id="reset_dag")
        
        task = Task(
            task_id="task1",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        dag.add_task(task)
        
        # Change states
        task.state = TaskState.SUCCESS
        dag.state = DAGState.SUCCESS
        
        # Reset
        dag.reset()
        
        assert task.state == TaskState.PENDING
        assert dag.state == DAGState.PENDING
    
    def test_dag_stats(self):
        """Test DAG statistics."""
        dag = DAG(dag_id="stats_dag")
        
        task1 = Task(
            task_id="task1",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        task2 = Task(
            task_id="task2",
            task_type="python",
            function="tests.conftest.simple_test_function",
            dependencies=["task1"]
        )
        
        dag.add_task(task1)
        dag.add_task(task2)
        
        # Set some states for testing
        task1.state = TaskState.SUCCESS
        task2.state = TaskState.FAILED
        
        stats = dag.get_stats()
        
        assert stats["total_tasks"] == 2
        assert stats["successful_tasks"] == 1
        assert stats["failed_tasks"] == 1
        assert stats["root_tasks"] == 1
        assert stats["leaf_tasks"] == 1
        assert stats["max_depth"] == 2
    
    def test_dag_to_dict(self):
        """Test DAG serialization to dictionary."""
        dag = DAG(
            dag_id="dict_dag",
            description="Test DAG",
            max_workers=3,
            execution_mode="multiprocessing"
        )
        
        task = Task(
            task_id="task1",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        dag.add_task(task)
        
        dag_dict = dag.to_dict()
        
        assert dag_dict["dag_id"] == "dict_dag"
        assert dag_dict["description"] == "Test DAG"
        assert dag_dict["max_workers"] == 3
        assert dag_dict["execution_mode"] == "multiprocessing"
        assert "task1" in dag_dict["tasks"]
        assert "stats" in dag_dict
    
    def test_dag_len(self):
        """Test DAG length."""
        dag = DAG(dag_id="len_dag")
        
        assert len(dag) == 0
        
        task = Task(
            task_id="task1",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        dag.add_task(task)
        assert len(dag) == 1
    
    def test_dag_contains(self):
        """Test DAG contains operation."""
        dag = DAG(dag_id="contains_dag")
        
        task = Task(
            task_id="task1",
            task_type="python",
            function="tests.conftest.simple_test_function"
        )
        
        dag.add_task(task)
        
        assert "task1" in dag
        assert "task2" not in dag
    
    def test_dag_repr(self):
        """Test DAG string representation."""
        dag = DAG(dag_id="repr_dag")
        
        repr_str = repr(dag)
        assert "repr_dag" in repr_str
        assert "tasks=0" in repr_str
        assert "pending" in repr_str
