# Quick Start Guide

This guide will help you get started with the Lightweight Task Runner with DAG Scheduling in just a few minutes.

## Installation

1. **Clone or download the project**
```bash
git clone <repository-url>
cd "Lightweight Task Runner with DAG Scheduling"
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

## Your First DAG

### Step 1: Validate Example Configuration

Test that everything is working by validating one of the included examples:

```bash
python -m task_runner validate --config examples/simple_dag.json
```

You should see:
```
✅ Configuration is valid!
```

### Step 2: Visualize the DAG

See what the DAG looks like:

```bash
python -m task_runner visualize --config examples/simple_dag.json
```

This shows the task structure and execution plan.

### Step 3: Run Your First DAG

Execute the simple example:

```bash
python -m task_runner run --config examples/simple_dag.json
```

You should see the tasks execute in sequence and complete successfully.

## Creating Your Own DAG

### Simple Example

Create a file called `my_first_dag.json`:

```json
{
  "dag_id": "my_first_dag",
  "description": "My first DAG",
  "max_workers": 2,
  "execution_mode": "threading",
  "tasks": [
    {
      "task_id": "hello_world",
      "task_type": "python",
      "function": "examples.tasks.hello_world",
      "args": ["World"],
      "retries": 1,
      "timeout": 30,
      "dependencies": []
    },
    {
      "task_id": "say_goodbye",
      "task_type": "shell",
      "command": "echo 'Goodbye from shell!'",
      "retries": 0,
      "timeout": 10,
      "dependencies": ["hello_world"]
    }
  ]
}
```

Then run it:

```bash
python -m task_runner run --config my_first_dag.json
```

## Available Commands

- **validate**: Check if your DAG configuration is valid
- **visualize**: See your DAG structure and execution plan
- **run**: Execute your DAG
- **status**: Check DAG execution status (for persistent storage setups)
- **logs**: View execution logs
- **list**: List available DAGs (for DAG registry setups)

## Key Concepts

### Tasks
- **Python tasks**: Execute Python functions
- **Shell tasks**: Run shell commands
- **Dependencies**: Tasks can depend on other tasks
- **Retries**: Automatic retry on failure
- **Timeouts**: Prevent hung tasks

### DAG Structure
```json
{
  "dag_id": "unique_name",
  "description": "What this DAG does",
  "max_workers": 4,
  "execution_mode": "threading",
  "tasks": [...]
}
```

### Task Structure
```json
{
  "task_id": "unique_task_name",
  "task_type": "python",
  "function": "module.function_name",
  "args": ["arg1", "arg2"],
  "kwargs": {"key": "value"},
  "retries": 2,
  "timeout": 60,
  "dependencies": ["other_task_id"]
}
```

## Examples Included

1. **simple_dag.json**: Basic sequential tasks
2. **complex_dag.json**: Advanced pipeline with parallel execution
3. **retry_dag.json**: Demonstrates retry logic
4. **shell_dag.json**: Shell command examples

Try them all:

```bash
python -m task_runner run --config examples/complex_dag.json
python -m task_runner run --config examples/shell_dag.json
```

## Next Steps

1. Read the full documentation in README.md
2. Explore the examples directory
3. Create your own task functions
4. Build complex workflows
5. Run tests: `python -m pytest`

## Getting Help

- Check the README.md for detailed documentation
- Look at examples for common patterns
- Run `python -m task_runner --help` for CLI help
- Use `python -m task_runner COMMAND --help` for command-specific help

Happy orchestrating! 
