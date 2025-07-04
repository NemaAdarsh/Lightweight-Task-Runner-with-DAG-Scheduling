import json
import importlib.util
import os
import logging
from typing import Dict, Any, List, Union
from ..core.dag import DAG
from ..core.task import Task


logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Handles loading and parsing of DAG configurations from various sources.
    
    Supports JSON configuration files and Python-based configuration modules.
    """
    
    @staticmethod
    def load_from_json(file_path: str) -> DAG:
        """
        Load DAG configuration from a JSON file.
        
        Args:
            file_path: Path to JSON configuration file
            
        Returns:
            Configured DAG instance
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration is invalid
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        logger.info(f"Loading DAG configuration from: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        
        return ConfigLoader._parse_config(config)
    
    @staticmethod
    def load_from_dict(config: Dict[str, Any]) -> DAG:
        """
        Load DAG configuration from a dictionary.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configured DAG instance
        """
        logger.info("Loading DAG configuration from dictionary")
        return ConfigLoader._parse_config(config)
    
    @staticmethod
    def load_from_python(module_path: str, config_var: str = "dag_config") -> DAG:
        """
        Load DAG configuration from a Python module.
        
        Args:
            module_path: Path to Python module
            config_var: Name of configuration variable in module
            
        Returns:
            Configured DAG instance
            
        Raises:
            FileNotFoundError: If module file doesn't exist
            AttributeError: If configuration variable doesn't exist
        """
        if not os.path.exists(module_path):
            raise FileNotFoundError(f"Python module not found: {module_path}")
        
        logger.info(f"Loading DAG configuration from Python module: {module_path}")
        
        # Load module dynamically
        spec = importlib.util.spec_from_file_location("config_module", module_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Cannot load module from: {module_path}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get configuration from module
        if not hasattr(module, config_var):
            raise AttributeError(f"Configuration variable '{config_var}' not found in module")
        
        config = getattr(module, config_var)
        return ConfigLoader._parse_config(config)
    
    @staticmethod
    def _parse_config(config: Dict[str, Any]) -> DAG:
        """
        Parse configuration dictionary into DAG instance.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configured DAG instance
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate required fields
        required_fields = ['dag_id', 'tasks']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field in configuration: {field}")
        
        # Extract DAG-level configuration
        dag_id = config['dag_id']
        description = config.get('description', '')
        max_workers = config.get('max_workers', 4)
        execution_mode = config.get('execution_mode', 'threading')
        
        # Create DAG instance
        dag = DAG(
            dag_id=dag_id,
            description=description,
            max_workers=max_workers,
            execution_mode=execution_mode
        )
        
        # Parse and add tasks
        tasks_config = config['tasks']
        if not isinstance(tasks_config, list):
            raise ValueError("'tasks' must be a list")
        
        # First pass: create all tasks
        tasks = {}
        for task_config in tasks_config:
            task = ConfigLoader._parse_task(task_config)
            tasks[task.task_id] = task
        
        # Second pass: add tasks to DAG (validates dependencies)
        for task in tasks.values():
            dag.add_task(task)
        
        logger.info(f"Successfully loaded DAG '{dag_id}' with {len(tasks)} tasks")
        return dag
    
    @staticmethod
    def _parse_task(task_config: Dict[str, Any]) -> Task:
        """
        Parse task configuration dictionary into Task instance.
        
        Args:
            task_config: Task configuration dictionary
            
        Returns:
            Configured Task instance
            
        Raises:
            ValueError: If task configuration is invalid
        """
        # Validate required fields
        required_fields = ['task_id', 'task_type']
        for field in required_fields:
            if field not in task_config:
                raise ValueError(f"Missing required field in task configuration: {field}")
        
        task_id = task_config['task_id']
        task_type = task_config['task_type']
        
        # Extract optional fields
        retries = task_config.get('retries', 0)
        timeout = task_config.get('timeout')
        dependencies = task_config.get('dependencies', [])
        
        # Validate dependencies is a list
        if not isinstance(dependencies, list):
            raise ValueError(f"Task '{task_id}': dependencies must be a list")
        
        # Type-specific validation and parameter extraction
        if task_type == 'python':
            if 'function' not in task_config:
                raise ValueError(f"Python task '{task_id}' must specify 'function'")
            
            function = task_config['function']
            args = task_config.get('args', [])
            kwargs = task_config.get('kwargs', {})
            
            # Validate function path format
            if not isinstance(function, str) or '.' not in function:
                raise ValueError(f"Task '{task_id}': function must be in format 'module.function'")
            
            task_kwargs = {
                'function': function,
                'args': args,
                'kwargs': kwargs
            }
            
        elif task_type == 'shell':
            if 'command' not in task_config:
                raise ValueError(f"Shell task '{task_id}' must specify 'command'")
            
            command = task_config['command']
            if not isinstance(command, str):
                raise ValueError(f"Task '{task_id}': command must be a string")
            
            task_kwargs = {
                'command': command
            }
            
        else:
            raise ValueError(f"Task '{task_id}': unsupported task type '{task_type}'")
        
        # Create task instance
        task = Task(
            task_id=task_id,
            task_type=task_type,
            retries=retries,
            timeout=timeout,
            dependencies=dependencies,
            **task_kwargs
        )
        
        return task
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> List[str]:
        """
        Validate configuration without creating DAG instance.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        try:
            # Try to parse configuration
            dag = ConfigLoader._parse_config(config)
            dag.validate()
            
        except Exception as e:
            errors.append(str(e))
        
        return errors
    
    @staticmethod
    def save_to_json(dag: DAG, file_path: str):
        """
        Save DAG configuration to JSON file.
        
        Args:
            dag: DAG instance to save
            file_path: Output file path
        """
        logger.info(f"Saving DAG configuration to: {file_path}")
        
        config = dag.to_dict()
        
        # Convert to JSON-serializable format
        json_config = {
            'dag_id': config['dag_id'],
            'description': config['description'],
            'max_workers': config['max_workers'],
            'execution_mode': config['execution_mode'],
            'tasks': [
                {
                    'task_id': task['task_id'],
                    'task_type': task['task_type'],
                    'retries': task['retries'],
                    'timeout': task['timeout'],
                    'dependencies': task['dependencies'],
                    **{k: v for k, v in task.items() 
                       if k not in ['task_id', 'task_type', 'retries', 'timeout', 'dependencies', 'state', 'current_attempt']}
                }
                for task in config['tasks'].values()
            ]
        }
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"DAG configuration saved successfully")


class ConfigValidator:
    """Utility class for validating DAG configurations."""
    
    @staticmethod
    def validate_json_file(file_path: str) -> List[str]:
        """
        Validate a JSON configuration file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            if not os.path.exists(file_path):
                errors.append(f"Configuration file not found: {file_path}")
                return errors
            
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            errors.extend(ConfigLoader.validate_config(config))
            
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return errors
    
    @staticmethod
    def validate_task_function(function_path: str) -> bool:
        """
        Validate that a Python function can be imported.
        
        Args:
            function_path: Function path in format 'module.function'
            
        Returns:
            True if function can be imported, False otherwise
        """
        try:
            module_path, function_name = function_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            func = getattr(module, function_name)
            return callable(func)
        except (ImportError, AttributeError, ValueError):
            return False
