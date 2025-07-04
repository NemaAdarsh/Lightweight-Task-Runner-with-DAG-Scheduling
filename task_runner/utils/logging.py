import logging
import os
from datetime import datetime
from typing import Optional


class TaskRunnerFormatter(logging.Formatter):
    """Custom formatter for task runner logs."""
    
    def __init__(self):
        super().__init__()
        self.base_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    def format(self, record):
        """Format log record with custom styling."""
        # Add color coding for different log levels (if terminal supports it)
        log_colors = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m'  # Magenta
        }
        reset_color = '\033[0m'
        
        if hasattr(record, 'task_id'):
            self.base_format = "%(asctime)s - %(name)s - %(levelname)s - [Task: %(task_id)s] - %(message)s"
        
        formatter = logging.Formatter(self.base_format)
        formatted_message = formatter.format(record)
        
        # Add color if running in terminal
        if os.isatty(1):  # Check if stdout is a terminal
            color = log_colors.get(record.levelname, '')
            formatted_message = f"{color}{formatted_message}{reset_color}"
        
        return formatted_message


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    task_id: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration for the task runner.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        console_output: Whether to output to console
        task_id: Optional task ID for context
        
    Returns:
        Configured logger instance
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger('task_runner')
    logger.setLevel(numeric_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Custom formatter
    formatter = TaskRunnerFormatter()
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        
        # Use plain format for file output
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Add task context if provided
    if task_id:
        logger = logging.LoggerAdapter(logger, {'task_id': task_id})
    
    return logger


def get_task_logger(task_id: str, base_logger: Optional[logging.Logger] = None) -> logging.Logger:
    """
    Get a logger with task context.
    
    Args:
        task_id: Task identifier
        base_logger: Base logger to use (creates new if None)
        
    Returns:
        Logger with task context
    """
    if base_logger is None:
        base_logger = logging.getLogger('task_runner')
    
    return logging.LoggerAdapter(base_logger, {'task_id': task_id})


def setup_dag_logging(dag_id: str, log_dir: str = "logs") -> logging.Logger:
    """
    Set up logging for a specific DAG execution.
    
    Args:
        dag_id: DAG identifier
        log_dir: Directory for log files
        
    Returns:
        Configured logger for the DAG
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{dag_id}_{timestamp}.log")
    
    return setup_logging(
        level="INFO",
        log_file=log_file,
        console_output=True
    )
