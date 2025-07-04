import networkx as nx
import logging
from typing import Dict, List, Optional, Set, Any
from .task import Task
from .state import DAGState, TaskState


logger = logging.getLogger(__name__)


class DAG:
    """
    Represents a Directed Acyclic Graph of tasks.
    
    The DAG manages task dependencies, validates the graph structure,
    and provides methods for topological sorting and execution planning.
    """
    
    def __init__(
        self,
        dag_id: str,
        description: str = "",
        max_workers: int = 4,
        execution_mode: str = "threading"
    ):
        """
        Initialize a new DAG.
        
        Args:
            dag_id: Unique identifier for the DAG
            description: Human-readable description
            max_workers: Maximum number of concurrent workers
            execution_mode: Execution mode ('threading' or 'multiprocessing')
        """
        self.dag_id = dag_id
        self.description = description
        self.max_workers = max_workers
        self.execution_mode = execution_mode
        self.state = DAGState.PENDING
        
        self.tasks: Dict[str, Task] = {}
        self.graph = nx.DiGraph()
        
        # Validate execution mode
        if execution_mode not in ['threading', 'multiprocessing']:
            raise ValueError(f"Invalid execution mode: {execution_mode}")
    
    def add_task(self, task: Task):
        """
        Add a task to the DAG.
        
        Args:
            task: Task instance to add
            
        Raises:
            ValueError: If task ID already exists
        """
        if task.task_id in self.tasks:
            raise ValueError(f"Task with ID '{task.task_id}' already exists")
        
        self.tasks[task.task_id] = task
        self.graph.add_node(task.task_id)
        
        # Add dependency edges
        for dependency in task.dependencies:
            if dependency not in self.tasks:
                logger.warning(
                    f"Dependency '{dependency}' for task '{task.task_id}' not found. "
                    "Ensure dependencies are added before dependent tasks."
                )
            self.graph.add_edge(dependency, task.task_id)
        
        logger.debug(f"Added task '{task.task_id}' to DAG '{self.dag_id}'")
    
    def remove_task(self, task_id: str):
        """
        Remove a task from the DAG.
        
        Args:
            task_id: ID of task to remove
            
        Raises:
            KeyError: If task ID doesn't exist
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task '{task_id}' not found in DAG")
        
        del self.tasks[task_id]
        self.graph.remove_node(task_id)
        
        logger.debug(f"Removed task '{task_id}' from DAG '{self.dag_id}'")
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.
        
        Args:
            task_id: ID of task to retrieve
            
        Returns:
            Task instance or None if not found
        """
        return self.tasks.get(task_id)
    
    def validate(self) -> bool:
        """
        Validate the DAG structure.
        
        Returns:
            True if DAG is valid, False otherwise
            
        Raises:
            ValueError: If DAG contains cycles or missing dependencies
        """
        logger.info(f"Validating DAG '{self.dag_id}'")
        
        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError(f"DAG '{self.dag_id}' contains cycles")
        
        # Check for missing dependencies
        missing_deps = []
        for task_id, task in self.tasks.items():
            for dep in task.dependencies:
                if dep not in self.tasks:
                    missing_deps.append(f"Task '{task_id}' depends on missing task '{dep}'")
        
        if missing_deps:
            raise ValueError(f"Missing dependencies in DAG '{self.dag_id}': {missing_deps}")
        
        # Check for orphaned nodes
        all_task_ids = set(self.tasks.keys())
        graph_nodes = set(self.graph.nodes())
        orphaned_nodes = graph_nodes - all_task_ids
        
        if orphaned_nodes:
            logger.warning(f"Found orphaned nodes in graph: {orphaned_nodes}")
            for node in orphaned_nodes:
                self.graph.remove_node(node)
        
        logger.info(f"DAG '{self.dag_id}' validation successful")
        return True
    
    def get_execution_order(self) -> List[List[str]]:
        """
        Get the topological execution order of tasks.
        
        Returns:
            List of task ID lists, where each inner list contains
            tasks that can be executed in parallel
        """
        if not self.validate():
            raise ValueError("Cannot get execution order for invalid DAG")
        
        # Get topological sort
        try:
            topo_order = list(nx.topological_sort(self.graph))
        except nx.NetworkXError as e:
            raise ValueError(f"Failed to compute topological order: {e}")
        
        # Group tasks by execution level
        execution_order = []
        remaining_tasks = set(topo_order)
        
        while remaining_tasks:
            # Find tasks with no unexecuted dependencies
            ready_tasks = []
            for task_id in remaining_tasks:
                dependencies = set(self.graph.predecessors(task_id))
                if dependencies.issubset(set(topo_order) - remaining_tasks):
                    ready_tasks.append(task_id)
            
            if not ready_tasks:
                raise ValueError("Unable to find executable tasks - possible circular dependency")
            
            execution_order.append(ready_tasks)
            remaining_tasks -= set(ready_tasks)
        
        logger.debug(f"Execution order for DAG '{self.dag_id}': {execution_order}")
        return execution_order
    
    def get_root_tasks(self) -> List[str]:
        """
        Get tasks with no dependencies (root tasks).
        
        Returns:
            List of task IDs with no dependencies
        """
        return [
            task_id for task_id, task in self.tasks.items()
            if not task.dependencies
        ]
    
    def get_leaf_tasks(self) -> List[str]:
        """
        Get tasks with no dependents (leaf tasks).
        
        Returns:
            List of task IDs with no dependents
        """
        all_dependencies = set()
        for task in self.tasks.values():
            all_dependencies.update(task.dependencies)
        
        return [
            task_id for task_id in self.tasks.keys()
            if task_id not in all_dependencies
        ]
    
    def get_task_dependencies(self, task_id: str) -> Set[str]:
        """
        Get all dependencies for a task (including transitive dependencies).
        
        Args:
            task_id: ID of task to get dependencies for
            
        Returns:
            Set of task IDs that the given task depends on
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task '{task_id}' not found in DAG")
        
        try:
            # Get all ancestors in the dependency graph
            ancestors = nx.ancestors(self.graph, task_id)
            return ancestors
        except nx.NetworkXError:
            return set()
    
    def get_task_dependents(self, task_id: str) -> Set[str]:
        """
        Get all dependents for a task (including transitive dependents).
        
        Args:
            task_id: ID of task to get dependents for
            
        Returns:
            Set of task IDs that depend on the given task
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task '{task_id}' not found in DAG")
        
        try:
            # Get all descendants in the dependency graph
            descendants = nx.descendants(self.graph, task_id)
            return descendants
        except nx.NetworkXError:
            return set()
    
    def reset(self):
        """Reset all tasks in the DAG to PENDING state."""
        for task in self.tasks.values():
            task.reset()
        self.state = DAGState.PENDING
        logger.info(f"Reset DAG '{self.dag_id}' to initial state")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the DAG.
        
        Returns:
            Dictionary containing DAG statistics
        """
        task_states = [task.state for task in self.tasks.values()]
        
        return {
            "dag_id": self.dag_id,
            "total_tasks": len(self.tasks),
            "pending_tasks": sum(1 for state in task_states if state == TaskState.PENDING),
            "running_tasks": sum(1 for state in task_states if state == TaskState.RUNNING),
            "successful_tasks": sum(1 for state in task_states if state == TaskState.SUCCESS),
            "failed_tasks": sum(1 for state in task_states if state == TaskState.FAILED),
            "skipped_tasks": sum(1 for state in task_states if state == TaskState.SKIPPED),
            "root_tasks": len(self.get_root_tasks()),
            "leaf_tasks": len(self.get_leaf_tasks()),
            "max_depth": len(self.get_execution_order()) if self.tasks else 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DAG to dictionary representation."""
        return {
            "dag_id": self.dag_id,
            "description": self.description,
            "max_workers": self.max_workers,
            "execution_mode": self.execution_mode,
            "state": self.state.value,
            "tasks": {
                task_id: task.to_dict()
                for task_id, task in self.tasks.items()
            },
            "stats": self.get_stats()
        }
    
    def __len__(self) -> int:
        return len(self.tasks)
    
    def __contains__(self, task_id: str) -> bool:
        return task_id in self.tasks
    
    def __repr__(self) -> str:
        return f"DAG(id={self.dag_id}, tasks={len(self.tasks)}, state={self.state.value})"
