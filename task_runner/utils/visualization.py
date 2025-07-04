import os
import shutil
from typing import Dict, List, Optional, Tuple
from ..core.dag import DAG
from ..core.task import Task
from ..core.state import TaskState


def visualize_dag_ascii(dag: DAG, show_states: bool = True) -> str:
    """
    Create ASCII visualization of DAG structure.
    
    Args:
        dag: DAG to visualize
        show_states: Whether to show task states
        
    Returns:
        ASCII representation of the DAG
    """
    if not dag.tasks:
        return "Empty DAG"
    
    lines = []
    lines.append(f"DAG: {dag.dag_id}")
    lines.append("=" * (len(dag.dag_id) + 5))
    lines.append("")
    
    # Get execution order for layout
    try:
        execution_order = dag.get_execution_order()
    except Exception:
        # Fallback to simple list if topological sort fails
        execution_order = [[task_id] for task_id in dag.tasks.keys()]
    
    # Create ASCII representation
    for level_idx, level_tasks in enumerate(execution_order):
        lines.append(f"Level {level_idx + 1}:")
        
        for task_id in level_tasks:
            task = dag.get_task(task_id)
            if not task:
                continue
            
            # Task representation
            state_symbol = _get_state_symbol(task.state) if show_states else ""
            task_line = f"  {state_symbol} {task_id} ({task.task_type})"
            
            # Add dependencies
            if task.dependencies:
                deps_str = ", ".join(task.dependencies)
                task_line += f" <- [{deps_str}]"
            
            lines.append(task_line)
        
        lines.append("")
    
    return "\n".join(lines)


def visualize_dag_tree(dag: DAG, show_states: bool = True) -> str:
    """
    Create tree-style visualization of DAG.
    
    Args:
        dag: DAG to visualize
        show_states: Whether to show task states
        
    Returns:
        Tree representation of the DAG
    """
    if not dag.tasks:
        return "Empty DAG"
    
    lines = []
    lines.append(f"DAG: {dag.dag_id}")
    lines.append("=" * (len(dag.dag_id) + 5))
    lines.append("")
    
    # Find root tasks (no dependencies)
    root_tasks = dag.get_root_tasks()
    
    if not root_tasks:
        lines.append("No root tasks found (possible cycle)")
        return "\n".join(lines)
    
    # Build tree representation
    visited = set()
    
    for root_task_id in root_tasks:
        _build_tree_recursive(dag, root_task_id, lines, "", visited, show_states)
    
    return "\n".join(lines)


def _build_tree_recursive(
    dag: DAG,
    task_id: str,
    lines: List[str],
    prefix: str,
    visited: set,
    show_states: bool
):
    """Recursively build tree representation."""
    if task_id in visited:
        return
    
    visited.add(task_id)
    task = dag.get_task(task_id)
    
    if not task:
        return
    
    # Task representation
    state_symbol = _get_state_symbol(task.state) if show_states else ""
    task_line = f"{prefix}{state_symbol} {task_id} ({task.task_type})"
    lines.append(task_line)
    
    # Find dependents (tasks that depend on this task)
    dependents = []
    for other_task_id, other_task in dag.tasks.items():
        if task_id in other_task.dependencies and other_task_id not in visited:
            dependents.append(other_task_id)
    
    # Recursively add dependents
    for i, dependent_id in enumerate(dependents):
        is_last = i == len(dependents) - 1
        child_prefix = prefix + ("└── " if is_last else "├── ")
        next_prefix = prefix + ("    " if is_last else "│   ")
        
        lines.append(child_prefix)
        _build_tree_recursive(dag, dependent_id, lines, next_prefix, visited, show_states)


def _get_state_symbol(state: TaskState) -> str:
    """Get symbol representation for task state."""
    symbols = {
        TaskState.PENDING: "⏳",
        TaskState.RUNNING: "🔄",
        TaskState.SUCCESS: "✅",
        TaskState.FAILED: "❌",
        TaskState.SKIPPED: "⏭️"
    }
    return symbols.get(state, "❓")


def print_dag_summary(dag: DAG) -> str:
    """
    Create summary of DAG statistics.
    
    Args:
        dag: DAG to summarize
        
    Returns:
        Summary string
    """
    stats = dag.get_stats()
    
    lines = []
    lines.append(f"DAG Summary: {dag.dag_id}")
    lines.append("=" * (len(dag.dag_id) + 13))
    lines.append(f"Description: {dag.description}")
    lines.append(f"Total Tasks: {stats['total_tasks']}")
    lines.append(f"Root Tasks: {stats['root_tasks']}")
    lines.append(f"Leaf Tasks: {stats['leaf_tasks']}")
    lines.append(f"Max Depth: {stats['max_depth']}")
    lines.append(f"Execution Mode: {dag.execution_mode}")
    lines.append(f"Max Workers: {dag.max_workers}")
    lines.append("")
    
    # Task state breakdown
    if stats['total_tasks'] > 0:
        lines.append("Task States:")
        lines.append(f"  Pending: {stats['pending_tasks']}")
        lines.append(f"  Running: {stats['running_tasks']}")
        lines.append(f"  Success: {stats['successful_tasks']}")
        lines.append(f"  Failed: {stats['failed_tasks']}")
        lines.append(f"  Skipped: {stats['skipped_tasks']}")
    
    return "\n".join(lines)


def print_execution_plan(dag: DAG) -> str:
    """
    Print the execution plan for a DAG.
    
    Args:
        dag: DAG to show execution plan for
        
    Returns:
        Execution plan string
    """
    lines = []
    lines.append(f"Execution Plan: {dag.dag_id}")
    lines.append("=" * (len(dag.dag_id) + 16))
    lines.append("")
    
    try:
        execution_order = dag.get_execution_order()
        
        for level_idx, level_tasks in enumerate(execution_order):
            lines.append(f"Execution Level {level_idx + 1}:")
            lines.append(f"  Tasks: {', '.join(level_tasks)}")
            lines.append(f"  Parallelizable: {len(level_tasks)} tasks")
            lines.append("")
        
        total_sequential_time = len(execution_order)
        total_tasks = sum(len(level) for level in execution_order)
        potential_speedup = total_tasks / total_sequential_time if total_sequential_time > 0 else 1
        
        lines.append(f"Summary:")
        lines.append(f"  Total execution levels: {len(execution_order)}")
        lines.append(f"  Maximum parallelism: {max(len(level) for level in execution_order) if execution_order else 0}")
        lines.append(f"  Potential speedup: {potential_speedup:.2f}x")
        
    except Exception as e:
        lines.append(f"Error generating execution plan: {e}")
    
    return "\n".join(lines)


def create_progress_bar(
    completed: int,
    total: int,
    width: int = 50,
    show_percentage: bool = True
) -> str:
    """
    Create a text-based progress bar.
    
    Args:
        completed: Number of completed items
        total: Total number of items
        width: Width of progress bar in characters
        show_percentage: Whether to show percentage
        
    Returns:
        Progress bar string
    """
    if total == 0:
        percentage = 100
        filled_width = width
    else:
        percentage = (completed / total) * 100
        filled_width = int(width * completed // total)
    
    bar = "█" * filled_width + "░" * (width - filled_width)
    
    if show_percentage:
        return f"[{bar}] {completed}/{total} ({percentage:.1f}%)"
    else:
        return f"[{bar}] {completed}/{total}"


def check_terminal_capabilities() -> Dict[str, bool]:
    """
    Check terminal capabilities for enhanced visualization.
    
    Returns:
        Dictionary of terminal capabilities
    """
    capabilities = {
        'color_support': False,
        'unicode_support': False,
        'width': 80,
        'height': 24
    }
    
    # Check if running in terminal
    if os.isatty(1):
        capabilities['color_support'] = True
        
        # Try to get terminal size
        try:
            size = shutil.get_terminal_size()
            capabilities['width'] = size.columns
            capabilities['height'] = size.lines
        except Exception:
            pass
        
        # Check unicode support (basic check)
        try:
            print("\u2713", end="", flush=True)
            print("\b \b", end="", flush=True)  # Clear the character
            capabilities['unicode_support'] = True
        except Exception:
            pass
    
    return capabilities
