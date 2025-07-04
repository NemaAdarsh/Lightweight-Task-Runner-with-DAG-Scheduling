import logging
from typing import List, Set, Dict, Any
from .dag import DAG
from .task import Task
from .state import TaskState


logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Handles task scheduling and dependency resolution for DAG execution.
    
    The scheduler determines which tasks are ready to run based on
    their dependencies and current state of other tasks.
    """
    
    def __init__(self, dag: DAG):
        """
        Initialize the scheduler with a DAG.
        
        Args:
            dag: DAG instance to schedule
        """
        self.dag = dag
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()
        self.running_tasks: Set[str] = set()
    
    def get_ready_tasks(self) -> List[Task]:
        """
        Get tasks that are ready to be executed.
        
        A task is ready if:
        1. It's in PENDING state
        2. All its dependencies have completed successfully
        3. It's not currently running
        
        Returns:
            List of tasks ready for execution
        """
        ready_tasks = []
        
        for task_id, task in self.dag.tasks.items():
            if self._is_task_ready(task):
                ready_tasks.append(task)
        
        logger.debug(f"Found {len(ready_tasks)} ready tasks: {[t.task_id for t in ready_tasks]}")
        return ready_tasks
    
    def _is_task_ready(self, task: Task) -> bool:
        """
        Check if a specific task is ready to run.
        
        Args:
            task: Task to check
            
        Returns:
            True if task is ready, False otherwise
        """
        # Task must be in PENDING state
        if task.state != TaskState.PENDING:
            return False
        
        # Task must not be currently running
        if task.task_id in self.running_tasks:
            return False
        
        # All dependencies must be completed successfully
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                # Check if dependency failed
                if dep_id in self.failed_tasks:
                    logger.info(f"Task {task.task_id} skipped due to failed dependency {dep_id}")
                    task.state = TaskState.SKIPPED
                    return False
                
                # Dependency not yet completed
                return False
        
        return True
    
    def mark_task_running(self, task_id: str):
        """
        Mark a task as currently running.
        
        Args:
            task_id: ID of task to mark as running
        """
        self.running_tasks.add(task_id)
        logger.debug(f"Marked task {task_id} as running")
    
    def mark_task_completed(self, task_id: str, success: bool):
        """
        Mark a task as completed.
        
        Args:
            task_id: ID of completed task
            success: Whether task completed successfully
        """
        self.running_tasks.discard(task_id)
        
        if success:
            self.completed_tasks.add(task_id)
            logger.debug(f"Marked task {task_id} as completed successfully")
        else:
            self.failed_tasks.add(task_id)
            logger.debug(f"Marked task {task_id} as failed")
            
            # Mark dependent tasks as skipped
            self._mark_dependents_skipped(task_id)
    
    def _mark_dependents_skipped(self, failed_task_id: str):
        """
        Mark all dependent tasks as skipped due to failed dependency.
        
        Args:
            failed_task_id: ID of failed task
        """
        dependents = self.dag.get_task_dependents(failed_task_id)
        
        for dep_task_id in dependents:
            task = self.dag.get_task(dep_task_id)
            if task and task.state == TaskState.PENDING:
                task.state = TaskState.SKIPPED
                logger.info(f"Task {dep_task_id} skipped due to failed dependency {failed_task_id}")
    
    def has_runnable_tasks(self) -> bool:
        """
        Check if there are any tasks that can still be run.
        
        Returns:
            True if there are runnable tasks, False otherwise
        """
        # Check if any tasks are ready to run
        if self.get_ready_tasks():
            return True
        
        # Check if any tasks are currently running
        if self.running_tasks:
            return True
        
        # Check if any tasks are still pending (might become ready later)
        pending_tasks = [
            task for task in self.dag.tasks.values()
            if task.state == TaskState.PENDING
        ]
        
        return len(pending_tasks) > 0
    
    def get_execution_plan(self) -> List[List[str]]:
        """
        Get the complete execution plan for the DAG.
        
        Returns:
            List of execution levels, where each level contains
            task IDs that can be executed in parallel
        """
        return self.dag.get_execution_order()
    
    def get_next_batch(self, max_tasks: int = None) -> List[Task]:
        """
        Get the next batch of tasks to execute.
        
        Args:
            max_tasks: Maximum number of tasks to return
            
        Returns:
            List of tasks ready for execution
        """
        ready_tasks = self.get_ready_tasks()
        
        if max_tasks is not None:
            ready_tasks = ready_tasks[:max_tasks]
        
        return ready_tasks
    
    def get_blocking_tasks(self, task_id: str) -> List[str]:
        """
        Get tasks that are blocking the execution of a specific task.
        
        Args:
            task_id: ID of task to check
            
        Returns:
            List of task IDs that are blocking the given task
        """
        task = self.dag.get_task(task_id)
        if not task:
            return []
        
        blocking_tasks = []
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks and dep_id not in self.failed_tasks:
                blocking_tasks.append(dep_id)
        
        return blocking_tasks
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Get execution progress information.
        
        Returns:
            Dictionary containing progress statistics
        """
        total_tasks = len(self.dag.tasks)
        completed = len(self.completed_tasks)
        failed = len(self.failed_tasks)
        running = len(self.running_tasks)
        skipped = sum(1 for task in self.dag.tasks.values() if task.state == TaskState.SKIPPED)
        pending = total_tasks - completed - failed - running - skipped
        
        progress_percentage = (completed + failed + skipped) / total_tasks * 100 if total_tasks > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "running_tasks": running,
            "skipped_tasks": skipped,
            "pending_tasks": pending,
            "progress_percentage": round(progress_percentage, 2)
        }
    
    def reset(self):
        """Reset the scheduler state."""
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        self.running_tasks.clear()
        logger.debug("Scheduler state reset")
    
    def __repr__(self) -> str:
        progress = self.get_progress()
        return (
            f"TaskScheduler("
            f"completed={progress['completed_tasks']}, "
            f"running={progress['running_tasks']}, "
            f"failed={progress['failed_tasks']}, "
            f"pending={progress['pending_tasks']}"
            f")"
        )
