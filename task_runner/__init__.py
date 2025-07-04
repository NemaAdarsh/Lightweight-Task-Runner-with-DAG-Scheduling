"""
Lightweight Task Runner with DAG Scheduling

A Python-based execution framework for dependent task orchestration.
"""

__version__ = "1.0.0"
__author__ = "Adarsh Nema"
__description__ = "Lightweight Task Runner with DAG Scheduling"

from .core.dag import DAG
from .core.task import Task
from .core.runner import TaskRunner
from .core.scheduler import TaskScheduler
from .core.state import TaskState, DAGState

__all__ = [
    "DAG",
    "Task", 
    "TaskRunner",
    "TaskScheduler",
    "TaskState",
    "DAGState"
]
