# Lightweight Task Runner with DAG Scheduling

A Python-based execution framework that allows users to define, schedule, and monitor dependent tasks in the form of a Directed Acyclic Graph (DAG). This tool enables developers to define tasks as Python functions or shell commands, specify dependencies between them, and execute them in the correct topological order.

## Features

- **DAG-based Task Orchestration**: Define tasks and their dependencies using directed acyclic graphs
- **Multiple Task Types**: Support for Python functions and shell commands
- **Parallel Execution**: Multithreading and multiprocessing support for concurrent task execution
- **Retry Logic**: Configurable retry mechanisms with exponential backoff
- **Timeout Management**: Task-level timeout configuration
- **Real-time Monitoring**: Track task states (PENDING, RUNNING, SUCCESS, FAILED)
- **Flexible Configuration**: JSON and Python-based DAG definitions
- **Command Line Interface**: Easy-to-use CLI for DAG execution and monitoring
- **Visualization**: Optional terminal-based DAG visualization
- **Comprehensive Logging**: Detailed audit trails and execution logs

## Architecture

The system consists of several core components:

### Core Components

1. **Task**: Individual executable units with retry logic and timeout handling
2. **DAG**: Container for tasks and their dependencies with validation
3. **TaskRunner**: Execution engine with parallel processing capabilities
4. **Scheduler**: Topological sorting and dependency resolution
5. **StateManager**: Task state tracking and transitions
6. **ConfigLoader**: JSON/Python configuration parsing and validation

### Task States

- **PENDING**: Task is waiting to be executed
- **RUNNING**: Task is currently executing
- **SUCCESS**: Task completed successfully
- **FAILED**: Task failed after all retries
- **SKIPPED**: Task was skipped due to failed dependencies

## Installation

1. Clone the repository:
```bash
git clone https://github.com/NemaAdarsh/Lightweight-Task-Runner-with-DAG-Scheduling.git
cd "Lightweight Task Runner with DAG Scheduling"
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Define a DAG using JSON

Create a DAG configuration file:

```json
{
  "dag_id": "example_dag",
  "description": "Example DAG with dependent tasks",
  "tasks": [
    {
      "task_id": "task_1",
      "task_type": "python",
      "function": "examples.tasks.hello_world",
      "args": ["World"],
      "kwargs": {},
      "retries": 3,
      "timeout": 30,
      "dependencies": []
    },
    {
      "task_id": "task_2",
      "task_type": "shell",
      "command": "echo 'Task 2 executing'",
      "retries": 1,
      "timeout": 10,
      "dependencies": ["task_1"]
    }
  ]
}
```

### 2. Run the DAG

```bash
python -m task_runner.cli run --config examples/example_dag.json
```

### 3. Monitor Execution

```bash
python -m task_runner.cli status --dag-id example_dag
```

## Configuration

### Task Configuration

Each task supports the following parameters:

- **task_id**: Unique identifier for the task
- **task_type**: Type of task ("python" or "shell")
- **function/command**: Function path or shell command to execute
- **args**: List of positional arguments
- **kwargs**: Dictionary of keyword arguments
- **retries**: Number of retry attempts (default: 0)
- **timeout**: Task timeout in seconds (default: None)
- **dependencies**: List of task IDs that must complete before this task

### DAG Configuration

- **dag_id**: Unique identifier for the DAG
- **description**: Human-readable description
- **tasks**: List of task configurations
- **max_workers**: Maximum number of concurrent workers (optional)
- **execution_mode**: "threading" or "multiprocessing" (default: "threading")

## Usage Examples

### Python Function Tasks

```python
# examples/tasks.py
def process_data(input_file, output_file):
    # Process data logic here
    return f"Processed {input_file} to {output_file}"

def validate_output(output_file):
    # Validation logic here
    return f"Validated {output_file}"
```

### Shell Command Tasks

```json
{
  "task_id": "backup_database",
  "task_type": "shell",
  "command": "pg_dump -h localhost -U user mydb > backup.sql",
  "retries": 2,
  "timeout": 300
}
```

### Complex DAG Example

```json
{
  "dag_id": "data_pipeline",
  "description": "Complete data processing pipeline",
  "max_workers": 4,
  "execution_mode": "threading",
  "tasks": [
    {
      "task_id": "extract_data",
      "task_type": "python",
      "function": "pipeline.extract.extract_from_source",
      "args": ["database"],
      "retries": 3,
      "timeout": 600,
      "dependencies": []
    },
    {
      "task_id": "transform_data",
      "task_type": "python",
      "function": "pipeline.transform.clean_and_transform",
      "dependencies": ["extract_data"],
      "retries": 2,
      "timeout": 300
    },
    {
      "task_id": "load_data",
      "task_type": "python",
      "function": "pipeline.load.load_to_warehouse",
      "dependencies": ["transform_data"],
      "retries": 1,
      "timeout": 180
    },
    {
      "task_id": "validate_pipeline",
      "task_type": "python",
      "function": "pipeline.validate.run_data_quality_checks",
      "dependencies": ["load_data"],
      "retries": 1,
      "timeout": 120
    }
  ]
}
```

## CLI Commands

### Run a DAG

```bash
python -m task_runner.cli run --config path/to/dag.json [--visualize]
```

### Check DAG Status

```bash
python -m task_runner.cli status --dag-id <dag_id>
```

### List All DAGs

```bash
python -m task_runner.cli list
```

### Validate DAG Configuration

```bash
python -m task_runner.cli validate --config path/to/dag.json
```

### View Logs

```bash
python -m task_runner.cli logs --dag-id <dag_id> [--task-id <task_id>]
```

## API Reference

### Core Classes

#### Task
```python
class Task:
    def __init__(self, task_id, task_type, retries=0, timeout=None, **kwargs):
        # Initialize task with configuration
        
    def execute(self) -> TaskResult:
        # Execute the task and return result
        
    def can_retry(self) -> bool:
        # Check if task can be retried
```

#### DAG
```python
class DAG:
    def __init__(self, dag_id, description="", tasks=None):
        # Initialize DAG with tasks
        
    def add_task(self, task: Task):
        # Add task to DAG
        
    def validate(self) -> bool:
        # Validate DAG for cycles and dependencies
        
    def get_execution_order(self) -> List[List[Task]]:
        # Get topologically sorted task execution order
```

#### TaskRunner
```python
class TaskRunner:
    def __init__(self, max_workers=4, execution_mode="threading"):
        # Initialize task runner
        
    def run_dag(self, dag: DAG) -> DAGResult:
        # Execute DAG and return results
        
    def run_task(self, task: Task) -> TaskResult:
        # Execute individual task
```

## Error Handling

The system provides comprehensive error handling:

- **Validation Errors**: Invalid DAG configurations are caught during parsing
- **Execution Errors**: Task failures are logged with detailed error messages
- **Dependency Errors**: Missing dependencies cause dependent tasks to be skipped
- **Timeout Errors**: Tasks exceeding timeout limits are terminated
- **Retry Logic**: Failed tasks are automatically retried based on configuration

## Logging

The system uses Python's logging module for comprehensive audit trails:

- **DAG Level**: DAG execution start/completion logs
- **Task Level**: Task state transitions and execution details
- **Error Level**: Detailed error messages and stack traces
- **Performance**: Execution timing and resource usage

## Testing

Run the test suite:

```bash
python -m pytest tests/ -v
```

Run specific test categories:

```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v

# End-to-end tests
python -m pytest tests/e2e/ -v
```

## Performance Considerations

- **Parallelism**: Use threading for I/O-bound tasks, multiprocessing for CPU-bound tasks
- **Memory Usage**: Monitor memory consumption for large DAGs
- **Task Granularity**: Balance between fine-grained and coarse-grained tasks
- **Resource Limits**: Set appropriate timeouts and retry limits

## Limitations

- **Single Machine**: Designed for local execution only
- **No Persistence**: Task state is not persisted across restarts
- **Basic Scheduling**: No advanced scheduling features like cron expressions
- **Simple UI**: Basic terminal-based visualization only

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by Apache Airflow's DAG concepts
- Built using NetworkX for graph operations
- Utilizes Python's concurrent.futures for parallel execution
