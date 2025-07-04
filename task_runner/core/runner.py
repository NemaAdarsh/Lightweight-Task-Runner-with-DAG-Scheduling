import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional
from .dag import DAG
from .task import Task
from .scheduler import TaskScheduler
from .state import DAGResult, TaskResult, DAGState, TaskState


logger = logging.getLogger(__name__)


class TaskRunner:
    """
    Executes DAGs with parallel task processing and state management.
    
    The TaskRunner handles the actual execution of tasks within a DAG,
    managing concurrency, monitoring progress, and collecting results.
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        execution_mode: str = "threading",
        poll_interval: float = 0.1
    ):
        """
        Initialize the task runner.
        
        Args:
            max_workers: Maximum number of concurrent workers
            execution_mode: Execution mode ('threading' or 'multiprocessing')
            poll_interval: Interval between progress checks in seconds
        """
        self.max_workers = max_workers
        self.execution_mode = execution_mode
        self.poll_interval = poll_interval
        
        # Validate execution mode
        if execution_mode not in ['threading', 'multiprocessing']:
            raise ValueError(f"Invalid execution mode: {execution_mode}")
        
        # State tracking
        self.running_dags: Dict[str, DAGResult] = {}
        self._shutdown_event = threading.Event()
    
    def run_dag(self, dag: DAG, blocking: bool = True) -> DAGResult:
        """
        Execute a complete DAG.
        
        Args:
            dag: DAG instance to execute
            blocking: Whether to wait for completion
            
        Returns:
            DAGResult containing execution results
        """
        logger.info(f"Starting execution of DAG: {dag.dag_id}")
        
        # Validate DAG before execution
        dag.validate()
        
        # Create result container
        result = DAGResult(dag.dag_id)
        result.start_time = datetime.now()
        result.state = DAGState.RUNNING
        
        # Store in running DAGs
        self.running_dags[dag.dag_id] = result
        
        try:
            if blocking:
                self._execute_dag_blocking(dag, result)
            else:
                # Start execution in background thread
                thread = threading.Thread(
                    target=self._execute_dag_blocking,
                    args=(dag, result),
                    daemon=True
                )
                thread.start()
                
        except Exception as e:
            logger.error(f"Error executing DAG {dag.dag_id}: {str(e)}")
            result.state = DAGState.FAILED
            result.end_time = datetime.now()
        
        return result
    
    def _execute_dag_blocking(self, dag: DAG, result: DAGResult):
        """
        Execute DAG in blocking mode.
        
        Args:
            dag: DAG to execute
            result: Result container to update
        """
        scheduler = TaskScheduler(dag)
        dag.state = DAGState.RUNNING
        
        # Use appropriate executor based on execution mode
        executor_class = ThreadPoolExecutor if self.execution_mode == 'threading' else ProcessPoolExecutor
        
        with executor_class(max_workers=self.max_workers) as executor:
            future_to_task = {}
            
            try:
                while scheduler.has_runnable_tasks() and not self._shutdown_event.is_set():
                    # Get ready tasks
                    ready_tasks = scheduler.get_ready_tasks()
                    
                    # Submit ready tasks for execution
                    for task in ready_tasks:
                        if len(future_to_task) < self.max_workers:
                            future = executor.submit(self._execute_task_wrapper, task)
                            future_to_task[future] = task
                            scheduler.mark_task_running(task.task_id)
                            logger.debug(f"Submitted task {task.task_id} for execution")
                    
                    # Check for completed tasks
                    if future_to_task:
                        # Wait for at least one task to complete
                        completed_futures = as_completed(future_to_task.keys(), timeout=self.poll_interval)
                        
                        try:
                            for future in completed_futures:
                                task = future_to_task[future]
                                del future_to_task[future]
                                
                                try:
                                    task_result = future.result()
                                    result.add_task_result(task_result)
                                    scheduler.mark_task_completed(task.task_id, task_result.success)
                                    
                                    if task_result.success:
                                        logger.info(f"Task {task.task_id} completed successfully")
                                    else:
                                        logger.error(f"Task {task.task_id} failed: {task_result.error}")
                                        
                                except Exception as e:
                                    logger.error(f"Error getting result for task {task.task_id}: {str(e)}")
                                    error_result = TaskResult(
                                        task_id=task.task_id,
                                        state=TaskState.FAILED,
                                        error=e
                                    )
                                    result.add_task_result(error_result)
                                    scheduler.mark_task_completed(task.task_id, False)
                                
                                break  # Process one completed task at a time
                                
                        except TimeoutError:
                            # No tasks completed within poll interval, continue
                            pass
                    else:
                        # No tasks running, wait a bit before checking again
                        time.sleep(self.poll_interval)
                
                # Wait for any remaining tasks to complete
                for future in future_to_task:
                    try:
                        task = future_to_task[future]
                        task_result = future.result(timeout=30)  # 30 second timeout for cleanup
                        result.add_task_result(task_result)
                        scheduler.mark_task_completed(task.task_id, task_result.success)
                    except Exception as e:
                        logger.error(f"Error during cleanup for task {task.task_id}: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error during DAG execution: {str(e)}")
                result.state = DAGState.FAILED
            
            finally:
                # Update final result state
                result.end_time = datetime.now()
                result.update_state()
                dag.state = result.state
                
                # Remove from running DAGs
                self.running_dags.pop(dag.dag_id, None)
                
                logger.info(
                    f"DAG {dag.dag_id} execution completed in {result.duration:.2f} seconds. "
                    f"State: {result.state.value}, Success rate: {result.success_rate:.2%}"
                )
    
    def _execute_task_wrapper(self, task: Task) -> TaskResult:
        """
        Wrapper for task execution with additional error handling.
        
        Args:
            task: Task to execute
            
        Returns:
            TaskResult from task execution
        """
        try:
            return task.execute()
        except Exception as e:
            logger.error(f"Unexpected error executing task {task.task_id}: {str(e)}")
            return TaskResult(
                task_id=task.task_id,
                state=TaskState.FAILED,
                error=e,
                start_time=datetime.now(),
                end_time=datetime.now()
            )
    
    def run_task(self, task: Task) -> TaskResult:
        """
        Execute a single task.
        
        Args:
            task: Task to execute
            
        Returns:
            TaskResult from task execution
        """
        logger.info(f"Executing single task: {task.task_id}")
        return self._execute_task_wrapper(task)
    
    def get_dag_status(self, dag_id: str) -> Optional[DAGResult]:
        """
        Get the current status of a running DAG.
        
        Args:
            dag_id: ID of DAG to check
            
        Returns:
            DAGResult if DAG is running, None otherwise
        """
        return self.running_dags.get(dag_id)
    
    def list_running_dags(self) -> List[str]:
        """
        Get list of currently running DAG IDs.
        
        Returns:
            List of DAG IDs currently executing
        """
        return list(self.running_dags.keys())
    
    def cancel_dag(self, dag_id: str) -> bool:
        """
        Cancel a running DAG.
        
        Args:
            dag_id: ID of DAG to cancel
            
        Returns:
            True if DAG was cancelled, False if not found
        """
        if dag_id in self.running_dags:
            logger.info(f"Cancelling DAG: {dag_id}")
            # Set shutdown event to stop execution
            self._shutdown_event.set()
            
            # Update result state
            result = self.running_dags[dag_id]
            result.state = DAGState.FAILED
            result.end_time = datetime.now()
            
            return True
        
        return False
    
    def shutdown(self):
        """Shutdown the task runner and cancel all running DAGs."""
        logger.info("Shutting down task runner")
        self._shutdown_event.set()
        
        # Update all running DAGs to failed state
        for result in self.running_dags.values():
            if result.state == DAGState.RUNNING:
                result.state = DAGState.FAILED
                result.end_time = datetime.now()
        
        self.running_dags.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get runner statistics.
        
        Returns:
            Dictionary containing runner statistics
        """
        return {
            "max_workers": self.max_workers,
            "execution_mode": self.execution_mode,
            "running_dags": len(self.running_dags),
            "poll_interval": self.poll_interval
        }
    
    def __repr__(self) -> str:
        return (
            f"TaskRunner("
            f"max_workers={self.max_workers}, "
            f"mode={self.execution_mode}, "
            f"running_dags={len(self.running_dags)}"
            f")"
        )
